import datetime

from flask import jsonify, request
from penn.base import APIError

from server import app, sqldb
from server.base import cached_route
from server.penndata import studyspaces, wharton
from server.studyspaces.book import get_wharton_sessionid, save_wharton_sessionid
from server.studyspaces.models import GSRRoomName


@app.route("/studyspaces/availability/<int:building>", methods=["GET"])
def parse_times_wrapper(building):
    """
    Returns JSON containing all rooms for a given building.

    Usage:
        /studyspaces/availability/<building> gives all rooms for the next 24 hours
        /studyspaces/availability/<building>?start=2018-25-01 gives all rooms in the start date
        /studyspaces/availability/<building>?start=...&end=... gives all rooms between the two days
    """
    if "date" in request.args:
        start = request.args.get("date")
        end = request.args.get("date")
    else:
        start = request.args.get("start")
        end = request.args.get("end")

    try:
        rooms = parse_times(building, start, end)
    except APIError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(rooms)


def parse_times(lid, start=None, end=None):
    if lid == 1:
        sessionid = get_wharton_sessionid(public=True)
        rooms = wharton.get_wharton_gsrs(sessionid, date=start)
        rooms = wharton.switch_format(rooms)
        save_wharton_sessionid()
    else:
        rooms = studyspaces.get_rooms(lid, start, end)
        rooms["location_id"] = rooms["id"]
        rooms["rooms"] = []
        for room_list in rooms["categories"]:
            for room in room_list["rooms"]:
                room["thumbnail"] = room["image"]
                del room["image"]
                room["room_id"] = room["id"]
                del room["id"]
                room["gid"] = room_list["cid"]
                room["lid"] = lid
                room["times"] = room["availability"]
                del room["availability"]
                for time in room["times"]:
                    time["available"] = True
                    time["start"] = time["from"]
                    time["end"] = time["to"]
                    del time["from"]
                    del time["to"]
                rooms["rooms"].append(room)
    return rooms


@app.route("/studyspaces/locations", methods=["GET"])
def display_id_pairs():
    """
    Returns JSON containing a list of buildings with their ids.
    """

    def get_data():
        return {
            "locations": studyspaces.get_buildings()
            + [{"lid": 1, "name": "Huntsman Hall", "service": "wharton"}]
        }

    return cached_route("studyspaces:locations", datetime.timedelta(days=1), get_data)


def get_room_name(lid, rid):
    """
    Returns the name of a given room ID
    """
    rooms = parse_times(lid)
    for room in rooms["rooms"]:
        if room["room_id"] == rid:
            new_name = GSRRoomName(lid=lid, gid=room["gid"], rid=rid, name=room["name"])
            sqldb.session.add(new_name)
            sqldb.session.commit()
            return room["name"]
    return None
