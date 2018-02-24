from flask import request, jsonify
from server import app
from os import getenv
import json

def return_options(x):
    return {"type": x}

@app.route('/homepage', methods=['GET'])
def get_homepage():
    with open('homepage_options.json') as json_file:
        data = json.load(json_file)
    cells = map(return_options, data['cellOptions'])
    return jsonify({
        "cells": cells
    })

@app.route('/homepage', methods=['POST'])
def change_order():
    cellOptions = request.get_json()
    authSecret = getenv('AUTH_SECRET')
    if (authSecret != request.headers.get('authSecret')):
        return "Please provide proper auth token with request."
    else:
        with open('homepage_options.json', 'w') as outfile:
            json.dump(cellOptions, outfile)
        return "Cell order successfully changed."

# TODO error check to ensure that cellOrder is only certain valid types
