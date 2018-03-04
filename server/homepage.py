from flask import request, jsonify
from server import app, sqldb
from os import getenv
from .models import User, DiningPreference, LaundryPreference, HomeCell
from sqlalchemy import func
import json

@app.route('/homepage', methods=['GET'])
def get_homepage():
    # Load options from json file
    # with open('homepage_options.json') as json_file:
    #    data = json.load(json_file)
    # Find user in database
    try:
        user = User.get_or_create()
    except ValueError as e:
        print(e)
        return jsonify({'err': ['error']})

    cell = get_popular_dining_cell(user)

    # Display information
    # cells = [{"type": x, "info": ""} for x in data['cellOptions']]
    cells = []
    diningCell = get_popular_dining_cell(user).getCell()
    cells.append(diningCell)

    laundryCells = [x.getCell() for x in get_laundry_cells(user)]
    cells.extend(laundryCells)

    gsrCell = get_study_spaces_cell().getCell()
    cells.append(gsrCell)

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
    venue_ids = [593, 747, 636, 1442]
    info = {"venues": venue_ids}
    cell = HomeCell("dining", info)
    return cell

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

# Error check request cell options
def error_options(options):
    with open('homepage_options.json') as json_file:
        data = json.load(json_file)
    for option in options:
        if (option not in data['cellOptions']):
            print('not', option)
            return True
    return False

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
