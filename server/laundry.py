from flask import jsonify
from server import app
from .penndata import *
from requests.exceptions import HTTPError


@app.route('/laundry/halls', methods=['GET'])
def all_halls():
    try:
        return jsonify({"halls": laundry.all_status()})
    except HTTPError:
        return jsonify({'error': 'The laundry api is currently unavailable.'})


@app.route('/laundry/hall/<hall_no>', methods=['GET'])
def hall(hall_no):
    try:
        return jsonify(laundry.hall_status(int(hall_no)))
    except HTTPError:
        return jsonify({'error': 'The laundry api is currently unavailable.'})

@app.route('/laundry/usage/<hall_no>', methods=['GET'])
def usage(hall_no):
    days = laundry.machine_usage(int(hall_no))
    try:
        return jsonify({"days": days})
    except HTTPError:
        return jsonify({'error': 'The laundry api is currently unavailable.'})