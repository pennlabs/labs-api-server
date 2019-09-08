import os
import datetime
import requests

from flask import jsonify, request
from dateutil.parser import parse

from server import app, db, sqldb
from penn.base import APIError
from ..models import StudySpacesBooking, User
from ..penndata import studyspaces, wharton
from ..base import cached_route


@app.route('/studyspaces/availability/<int:building>', methods=['GET'])
def parse_times(building):
    """
    Returns JSON containing all rooms for a given building.

    Usage:
        /studyspaces/availability/<building> gives all rooms for the next 24 hours
        /studyspaces/availability/<building>?start=2018-25-01 gives all rooms in the start date
        /studyspaces/availability/<building>?start=...&end=... gives all rooms between the two days
    """
    if 'date' in request.args:
        start = request.args.get('date')
        end = request.args.get('date')
    else:
        start = request.args.get('start')
        end = request.args.get('end')

    if building == 1:
        sessionid = get_wharton_sessionid(public=True)
        try:
            rooms = wharton.get_wharton_gsrs(sessionid, date=start)
            rooms = wharton.switch_format(rooms)
            save_wharton_sessionid()
        except APIError as e:
            return jsonify({"error": str(e)}), 400
    else:
        try:
            rooms = studyspaces.get_rooms(building, start, end)
            rooms["location_id"] = rooms["id"]
            rooms["rooms"] = []
            for room_list in rooms["categories"]:
                for room in room_list["rooms"]:
                    room["thumbnail"] = room["image"]
                    del room["image"]
                    room["room_id"] = room["id"]
                    del room["id"]
                    room["gid"] = room_list["cid"]
                    room["lid"] = building
                    room["times"] = room["availability"]
                    del room["availability"]
                    for time in room["times"]:
                        time["available"] = True
                        time["start"] = time["from"]
                        time["end"] = time["to"]
                        del time["from"]
                        del time["to"]
                    rooms["rooms"].append(room)
        except APIError as e:
            return jsonify({"error": str(e)}), 400
    return jsonify(rooms)


@app.route('/studyspaces/locations', methods=['GET'])
def display_id_pairs():
    """
    Returns JSON containing a list of buildings with their ids.
    """
    def get_data():
        return {"locations": studyspaces.get_buildings() + [{"lid": 1, "name": "Huntsman Hall", "service": "wharton"}]}

    return cached_route('studyspaces:locations', datetime.timedelta(days=1), get_data)
