import datetime

from flask import jsonify, request
from server import app
from .penndata import studyspaces
from .base import cached_route


@app.route('/studyspaces/availability/<int:building>', methods=['GET'])
def parse_times(building):
    """
    Returns JSON containing all rooms for a given building.

    Usage:
        /studyspaces/availability/<building> gives all rooms for the next 24 hours
        /studyspaces/availability/<building>?start=2018-25-01T11:00:00-0500 gives all rooms from start to 24 hours later
        /studyspaces/availability/<building>?start=...&end=... gives all rooms between the two times
    """
    show_available = request.args.get("available")
    if show_available is not None:
        show_available = show_available.lower() == "true"

    if 'date' in request.args:
        date = datetime.datetime.strptime(request.args.get('date'), "%Y-%m-%d")
        date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        start = date
        end = date + datetime.timedelta(days=1)
    else:
        date = datetime.datetime.now()
        try:
            start = request.args.get('start')
            if start is not None:
                start = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S%z")
                # round down to closest hour
                start = start.replace(minute=0, second=0, microsecond=0)
            else:
                start = date
            end = request.args.get('end')
            if end is not None:
                end = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%S%z")
            else:
                end = start + datetime.timedelta(days=1)
                # stop at midnight today
                end = end.replace(hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            return jsonify({"error": "Incorrect date format!"})

    rooms = studyspaces.get_rooms(building, start, end)

    if show_available is not None:
        modified_rooms = []
        for room in rooms:
            room["times"] = [x for x in room["times"] if x["available"] == show_available]
            if len(room["times"]) > 0:
                modified_rooms.append(room)
        rooms = modified_rooms

    return jsonify({
        "location_id": building,
        "date": start.strftime("%Y-%m-%d"),
        "rooms": rooms
    })


@app.route('/studyspaces/locations', methods=['GET'])
def display_id_pairs():
    """
    Returns JSON containing a list of buildings with their ids.
    """
    def get_data():
        return {"locations": studyspaces.get_buildings()}

    return cached_route('studyspaces:locations', datetime.timedelta(days=1), get_data)


@app.route('/studyspaces/book', methods=['POST'])
def book_room():
    """
    Books a room.
    """

    try:
        building = int(request.form["building"])
        room = int(request.form["room"])
    except KeyError, ValueError:
        return jsonify({"error": "Please specify a correct building and room id!"})

    start = datetime.datetime.strptime(request.form["start"], "%Y-%m-%dT%H:%M:%S%z")
    end = datetime.datetime.strptime(request.form["end"], "%Y-%m-%dT%H:%M:%S%z")

    contact = {}
    for field in ["firstname", "lastname", "email", "groupname", "phone", "size"]:
        try:
            contact[field] = request.form[field]
        except KeyError:
            return jsonify({"error": "'{}' is a required parameter!".format(field)})

    try:
        flag = studyspaces.book_room(building, room, start, end, **contact)
        return jsonify({"success": flag})
    except ValueError as e:
        return jsonify({"error": str(e)})
