import datetime

from flask import jsonify
from server import app
from .penndata import studyspaces


@app.route('/studyspaces/<int:building>', methods=['GET'])
def parse_times(building):
    """
    Returns JSON containing all rooms for a given building.

    Usage:
        /studyspaces/<building> gives all rooms for today
    """
    date = datetime.date.today()
    return jsonify({
        "location_id": building,
        "date": date.strftime("%Y-%m-%d"),
        "rooms": studyspaces.get_rooms(building, date, date + datetime.timedelta(days=1))
    })


@app.route('/studyspaces/', methods=['GET'])
def display_id_pairs():
    """
    Returns JSON containing a list of buildings with their ids.
    """
    return jsonify({"locations": studyspaces.get_buildings()})
