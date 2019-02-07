import os
import datetime
import requests

from flask import jsonify, request
from dateutil.parser import parse

from server import app, sqldb
from penn.base import APIError
from .models import StudySpacesBooking, User
from .penndata import studyspaces, wharton
from .base import cached_route


@app.route('/studyspaces/gsr', methods=['GET'])
def get_wharton_gsrs():
    """ Temporary endpoint to allow non-authenticated users to access the list of GSRs. """

    sessionid = request.args.get('sessionid')

    if not sessionid:
        sessionid = os.environ.get('GSR_SESSIONID')

    if not sessionid:
        return jsonify({'error': 'No GSR session id is set!'})

    time = request.args.get('date')

    if time:
        time += " 05:00"
    else:
        time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%S")

    resp = requests.get('https://apps.wharton.upenn.edu/gsr/api/app/grid_view/', params={
        'search_time': time
    }, cookies={
        'sessionid': sessionid
    })
    if resp.status_code == 200:
        return jsonify(resp.json())
    else:
        return jsonify({'error': 'Remote server returned status code {}.'.format(resp.status_code)})


@app.route('/studyspaces/gsr/reservations', methods=['GET'])
def get_wharton_gsr_reservations():
    """
    Returns JSON containing a list of Wharton GSR reservations.
    """

    sessionid = request.args.get('sessionid')

    if not sessionid:
        return jsonify({'error': 'No Session ID provided.'})

    try:
        reservations = wharton.get_reservations(sessionid)
    except APIError as e:
        return jsonify({"error": str(e)})

    return jsonify({'reservations': reservations})


@app.route('/studyspaces/gsr/reservations', methods=['GET'])
def get_wharton_gsr_reservations():
    """
    Returns JSON containing a list of Wharton GSR reservations.
    """

    sessionid = request.args.get('sessionid')

    if not sessionid:
        return jsonify({'error': 'No Session ID provided.'})

    try:
        reservations = wharton.get_reservations(sessionid)
    except APIError as e:
        return jsonify({"error": str(e)})

    return jsonify({'reservations': reservations})


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

    try:
        rooms = studyspaces.get_rooms(building, start, end)

        # legacy support for old scraping method
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
        return jsonify({"error": str(e)})

    return jsonify(rooms)


@app.route('/studyspaces/locations', methods=['GET'])
def display_id_pairs():
    """
    Returns JSON containing a list of buildings with their ids.
    """
    def get_data():
        return {"locations": studyspaces.get_buildings()}

    return cached_route('studyspaces:locations', datetime.timedelta(days=1), get_data)


@app.route('/studyspaces/cancel', methods=['POST'])
def cancel_room():
    """
    Cancels a booked room.
    """
    booking_id = request.form.get("booking_id")
    if not booking_id:
        return jsonify({"error": "No booking id sent to server!"})

    # ensure that the server was the one that booked the room
    for bid in booking_id.strip().split(","):
        exists = sqldb.session.query(sqldb.exists().where(StudySpacesBooking.booking_id == bid)).scalar()
        if not exists:
            return jsonify({"error": "Cancellation request aborted because of booking '{}'.".format(bid)})

    resp = studyspaces.cancel_room(booking_id)
    return jsonify(resp)


@app.route('/studyspaces/book', methods=['POST'])
def book_room():
    """
    Books a room.
    """

    try:
        room = int(request.form["room"])
    except (KeyError, ValueError):
        return jsonify({"results": False, "error": "Please specify a correct room id!"})

    try:
        start = parse(request.form["start"])
        end = parse(request.form["end"])
    except KeyError:
        return jsonify({"results": False, "error": "No start and end parameters passed to server!"})

    contact = {}
    for arg, field in [("fname", "firstname"), ("lname", "lastname"), ("email", "email"), ("nickname", "groupname")]:
        try:
            contact[arg] = request.form[field]
        except KeyError:
            return jsonify({"results": False, "error": "'{}' is a required parameter!".format(field)})

    contact["custom"] = {}
    for arg, field in [("q2533", "phone"), ("q2555", "size"), ("q2537", "size")]:
        try:
            contact["custom"][arg] = request.form[field]
        except KeyError:
            pass

    resp = studyspaces.book_room(room, start.isoformat(), end.isoformat(), **contact)
    if "error" not in resp:
        save_booking(
            rid=room,
            email=contact["email"],
            start=start.replace(tzinfo=None),
            end=end.replace(tzinfo=None),
            booking_id=resp.get("booking_id")
        )
    return jsonify(resp)


def save_booking(**info):
    try:
        user = User.get_or_create()
    except ValueError:
        user = None

    if user is None:
        return

    info['user'] = user.id

    item = StudySpacesBooking(**info)

    sqldb.session.add(item)
    sqldb.session.commit()
