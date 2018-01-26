import datetime

from flask import jsonify, request
from server import app
from .penndata import studyspaces


@app.route('/studyspaces/<int:building>', methods=['GET'])
def parse_times(building):
    """
    Returns JSON containing all rooms for a given building.

    Usage:
        /studyspaces/<building> gives all rooms for the next 24 hours
        /studyspaces/<building>?start=2018-25-01T11:00:00-0500 gives all rooms from start to 24 hours later
        /studyspaces/<building>?start=...&end=... gives all rooms between the two times
    """
    date = datetime.datetime.now()
    start = request.args.get('start')
    if start is not None:
        start = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S%z")
    else:
        start = date
    end = request.args.get('end')
    if end is not None:
        end = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%S%z")
    else:
        end = start + datetime.timedelta(days=1)
    return jsonify({
        "location_id": building,
        "date": date.strftime("%Y-%m-%d"),
        "rooms": studyspaces.get_rooms(building, start, end)
    })


@app.route('/studyspaces/', methods=['GET'])
def display_id_pairs():
    """
    Returns JSON containing a list of buildings with their ids.
    """
    return jsonify({"locations": studyspaces.get_buildings()})
