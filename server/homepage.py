from flask import request, jsonify
from server import app, sqldb
from os import getenv
from .models import User, DiningPreference
from sqlalchemy import func
import json

@app.route('/homepage', methods=['GET'])
def get_homepage():
    # Load options from json file
    with open('homepage_options.json') as json_file:
        data = json.load(json_file)
    # Find user in database
    try:
        user = User.get_or_create()
    except ValueError as e:
        print(e)
        return jsonify({'err': ['error']})

    preferences = sqldb.session.query(DiningPreference.venue_id, func.count(DiningPreference.venue_id)) \
                               .filter_by(user_id=user.id).group_by(DiningPreference.venue_id).all()
    preference_arr = [x[0] for x in preferences]
    # Display information
    cells = [{"type": x, "info": ""} for x in data['cellOptions']]
    for x in cells:
        if x["type"] == 'dining':
            x["info"] = {'visited_halls': preference_arr}
    return jsonify({
        "cells": cells
    })

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
