from flask import request, jsonify
from server import app, sqldb
from os import getenv
from .models import User, DiningPreference, LaundryPreference, HomeCell, HomeCellOrder, Event
from sqlalchemy import func
import json

@app.route('/homepage', methods=['GET'])
def get_homepage():
    # Find user in database
    try:
        user = User.get_or_create()
    except ValueError as e:
        print(e)
        return jsonify({'err': [str(e)]})

    cell = get_popular_dining_cell(user)

    # Display information
    cells = []
    diningCell = get_popular_dining_cell(user).getCell()
    cells.append(diningCell)

    laundryCells = [x.getCell() for x in get_laundry_cells(user)]
    cells.extend(laundryCells)

    gsrCell = get_study_spaces_cell().getCell()
    cells.append(gsrCell)

    newsCell = get_news_cell().getCell()
    cells.append(newsCell)

    if get_event_cell():
        eventCell = get_event_cell().getCell()
        cells.append(eventCell)

    response = jsonify({"cells": cells})
    response.status_code = 200 # or 400 or whatever
    return response

# returns a dining cell containing the users preferences in sorted order
def get_dining_preference_cell(user):
    preferences = sqldb.session.query(DiningPreference.venue_id) \
                               .filter_by(user_id=user.id).group_by(DiningPreference.venue_id) \
                               .order_by(func.count(DiningPreference.venue_id).desc()).all()
    venue_ids = [x.venue_id for x in preferences]
    return HomeCell("dining", info)

# returns a dining cell
# TODO: personalize with preferences
def get_popular_dining_cell(user):
    venue_ids = [593, 747, 636]
    info = {"venues": venue_ids}
    return HomeCell("dining", info)

# returns a list of laundry cells
def get_laundry_cells(user):
    preferences = LaundryPreference.query.filter_by(user_id=user.id)
    room_ids = [x.room_id for x in preferences]

    # If the user has no preferences, select Bishop White
    if len(room_ids) == 0:
        room_ids.append(0)

    return [HomeCell("laundry", { "room_id": x }) for x in room_ids]

# returns a study spaces cell
def get_study_spaces_cell():
    return HomeCell("studyRoomBooking", None)

# returns a news cell
# TODO: Dynamically fetch news item from database or from website
def get_news_cell():
    source = "The Daily Pennsylvanian"
    title = "Penn's cost of attendance will exceed $70,000 next year - a 3.8 percent increase"
    date = "2018-03-01T19:12:00-05:00"
    imageUrl = "http://snworksceo.imgix.net/dpn/66799ad7-5e72-4759-9d4e-33a62308bdce.sized-1000x1000.jpg"
    articleUrl = "http://www.thedp.com/article/2018/03/university-penn-president-amy-gutmann-wendell-pritchett-budget-board-trustees-tuition-increase-financial-aid"
    info = {"source": source, "title": title, "date": date, "imageUrl": imageUrl, "articleUrl": articleUrl}
    return HomeCell("news", info)

# return a event cell
# TODO Fetch most recent, most popular, etc
def get_event_cell():
    event = Event.query.first()
    if event:
        info = {
            'name': event.name,
            'description': event.description,
            'image_url': event.image_url,
            'start_time': event.start_time,
            'end_time': event.end_time,
            'email': event.email,
            'website': event.website,
            'facebook': event.facebook
        }
        return HomeCell("event", info)
    else:
        return None

# Error check request cell options
def error_options(options):
    with open('homepage_options.json') as json_file:
        data = json.load(json_file)
    for option in options:
        if (option not in data['cellOptions']):
            print('not', option)
            return True
    return False

@app.route('/homepage/order', methods=['GET'])
def get_order():
    cell_options = HomeCellOrder.query.all()
    options = [
        x.cell_type
     for x in cell_options]
    return jsonify({'cells': options})

@app.route('/homepage/order', methods=['POST'])
def change_cell_order():
    cell_options = request.get_json()['cellOptions']

    # delete old homepage order
    HomeCellOrder.query.all().delete()

    # add new order
    for cell_option in cell_options:
        print('opt', cell_option)
        home_order = HomeCellOrder(cell_type=cell_option)
        sqldb.session.add(home_order)
    sqldb.session.commit()
    return jsonify({'success': True})


@app.route('/homepage', methods=['POST'])
def change_order():
    cellOptions = request.get_json()
    authSecret = getenv('AUTH_SECRET')
    if (authSecret != request.headers.get('authSecret')):
        return "Please provide proper auth token with request."
    elif error_options(cellOptions['cellOptions']):
        return "Not all cell options are valid."
    else:
        with open('homepage_options.json', 'w') as outfile:
            json.dump(cellOptions, outfile)
        return "Cell order successfully changed."

# TODO Add an info field to what is returned from get request. For now, info will
# contain all rooms that a user has ever been in
