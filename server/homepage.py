from flask import request, jsonify
from server import app, sqldb
from os import getenv
from .models import User, DiningPreference, LaundryPreference, HomeCell, HomeCellOrder, Event
from .calendar3year import pull_todays_calendar
from sqlalchemy import func
from .news import fetch_frontpage_article
import json
import pytz

utc = pytz.timezone('UTC')
eastern = pytz.timezone('US/Eastern')

@app.route('/homepage', methods=['GET'])
def get_homepage():
    # Find user in database
    try:
        user = User.get_or_create()
    except ValueError as e:
        response = jsonify({'err': [str(e)]})
        response.status_code = 400
        return response

    # Display information
    cells = []

    ##### Adam's Dynamic Cell Code for changing order remotely #####

    # cell_options = HomeCellOrder.query.all()
    # options = [
    #     x.cell_type
    #  for x in cell_options]

    # print('options', options)

    # for option in options:
    #     if option == 'Laundry':
    #         print('yay laundry', option)
    #         laundryCell = get_top_laundry_cell(user).getCell()
    #         cells.append(laundryCell)
    #     elif option == 'Dining':
    #         print('yay dining', option)
    #         diningCell = get_popular_dining_cell(user).getCell()
    #         cells.append(diningCell)
    #     elif option == 'News':
    #         newsCell = get_news_cell().getCell()
    #         cells.append(newsCell)
    #     elif option == 'Event':
    #         if get_event_cell():
    #             eventCell = get_event_cell().getCell()
    #             cells.append(eventCell)
    #     elif option == 'GSR':
    #         gsrCell = get_study_spaces_cell().getCell()
    #         cells.append(gsrCell)
    #     else:
    #         print('other', option)

    laundry = get_top_laundry_cell(user)
    dining = get_dining_cell(user)
    news = get_news_cell()
    gsr = get_study_spaces_cell()
    calendar = get_university_event_cell()

    if calendar is not None:
        cells.append(calendar)

    cells.append(dining)

    if news is not None:
        cells.append(news)
    
    cells.extend([gsr, laundry])

    response = jsonify({"cells": [x.getCell() for x in cells]})
    response.status_code = 200
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
def get_dining_cell(user):
    preferences = sqldb.session.query(DiningPreference.venue_id).filter_by(user_id=user.id)
    venue_ids = [x.venue_id for x in preferences]
    defaults_ids = [593, 1442, 636]
    if len(venue_ids) == 0:
        venue_ids = defaults_ids
    elif len(venue_ids) == 1:
        venue_ids.extend(defaults_ids)
        venue_ids = list(set(venue_ids))[:3]

    info = {"venues": venue_ids}
    return HomeCell("dining", info)

# returns a list of laundry cells
def get_laundry_cells(user):
    preferences = LaundryPreference.query.filter_by(user_id=user.id)
    room_ids = [x.room_id for x in preferences]

    # If the user has no preferences, select Bishop White
    if not room_ids:
        room_ids.append(0)

    return [HomeCell("laundry", { "room_id": x }) for x in room_ids]

# returns user's top laundry cell
def get_top_laundry_cell(user):
    top_preference = LaundryPreference.query.filter_by(user_id=user.id).first()
    # If no top choice, select bishop white
    if top_preference:
        return HomeCell("laundry", { "room_id": top_preference.room_id})
    return HomeCell("laundry", { "room_id": 0})

# returns a study spaces cell
def get_study_spaces_cell():
    return HomeCell("studyRoomBooking", None)

# returns a university notification cell
def get_university_event_cell():
    calendar = pull_todays_calendar()
    if calendar:
        return HomeCell("calendar", calendar)
    else:
        return None

# returns a news cell
# TODO: Dynamically fetch news item from database or from website
def get_news_cell():
    article = fetch_frontpage_article()
    if article:
        return HomeCell("news", article)
    else:
        return None
    
# return a event cell
# TODO Fetch most recent, most popular, etc
def get_event_cell():
    event = Event.query.first()
    if event:
        info = {
            'name': event.name,
            'description': event.description,
            'image_url': event.image_url,
            'start_time': utc.localize(event.start_time).astimezone(eastern).isoformat(),
            'end_time': utc.localize(event.end_time).astimezone(eastern).isoformat(),
            'email': event.email,
            'website': event.website,
            'facebook': event.facebook
        }
        return HomeCell("event", info)
    else:
        return None

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
    HomeCellOrder.query.delete()

    # add new order
    for cell_option in cell_options:
        print('opt', cell_option)
        home_order = HomeCellOrder(cell_type=cell_option)
        sqldb.session.add(home_order)
    sqldb.session.commit()
    return jsonify({'success': True})
