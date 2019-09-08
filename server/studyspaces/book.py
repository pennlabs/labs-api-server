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
from .book import get_reservations


def get_wharton_sessionid(public=False):
    """ Try to get a GSR session id. """
    sessionid = request.args.get('sessionid')
    cache_key = 'studyspaces:gsr:sessionid'

    if sessionid:
        return sessionid

    if public:
        if db.exists(cache_key):
            return db.get(cache_key).decode('utf8')

        return os.environ.get('GSR_SESSIONID')

    return None


def save_wharton_sessionid():
    sessionid = request.args.get('sessionid')
    cache_key = 'studyspaces:gsr:sessionid'

    if sessionid:
        db.set(cache_key, sessionid, ex=604800)


@app.route('/studyspaces/book', methods=['POST'])
def book_room():
    """
    Books a room.
    """
    try:
        room = int(request.form["room"])
    except (KeyError, ValueError):
        return jsonify({"results": False, "error": "Please specify a correct room id!"}), 400

    try:
        start = parse(request.form["start"])
        end = parse(request.form["end"])
    except KeyError:
        return jsonify({"results": False, "error": "No start and end parameters passed to server!"}), 400

    try:
        lid = int(request.form["lid"])
    except (KeyError, ValueError):
        lid = None

    email = None

    if lid == 1:
        sessionid = request.form.get("sessionid")
        if not sessionid:
            return jsonify({"results": False, "error": "You must pass a sessionid when booking a Wharton GSR!"}), 400
        resp = wharton.book_reservation(sessionid, room, start, end)
        resp["results"] = resp["success"]
        room_booked = resp["success"]
        del resp["success"]
        if room_booked:
            save_wharton_sessionid()
            booking_id = None

            # Look up the reservation to get the booking id
            reservations = get_reservations(None, sessionid, 0)
            startStr = request.form["start"].split("-")[0]
            endStr = request.form["end"].split("-")[0]
            for reservation in reservations:
                resStartStr = reservation["fromDate"].split("-")[0]
                resEndStr = reservation["toDate"].split("-")[0]
                if startStr == resStartStr and endStr == resEndStr:
                    booking_id = reservation["booking_id"]
                    break
    else:
        contact = {}
        for arg, field in [("fname", "firstname"), ("lname", "lastname"), ("email", "email"), ("nickname", "groupname")]:
            try:
                contact[arg] = request.form[field]
            except KeyError:
                return jsonify({"results": False, "error": "'{}' is a required parameter!".format(field)})

        email = contact.get("email")
        contact["custom"] = {}
        contact["custom"]["q3699"] = get_affiliation(email)
        for arg, field in [("q2533", "phone"), ("q2555", "size"), ("q2537", "size"), ("q3699", "affiliation")]:
            try:
                contact["custom"][arg] = request.form[field]
            except KeyError:
                pass

        resp = studyspaces.book_room(room, start.isoformat(), end.isoformat(), **contact)
        room_booked = resp.get("results")
        booking_id = resp.get("booking_id")

    try:
        user = User.get_user()
        user_id = user.id
        if email and user.email != email:
            user.email = email
            sqldb.session.commit()
        else:
            email = user.email
    except ValueError:
        user_id = None

    if room_booked:
        save_booking(
            lid=lid,
            rid=room,
            email=email,
            start=start.replace(tzinfo=None),
            end=end.replace(tzinfo=None),
            booking_id=booking_id,
            user=user_id
        )
    return jsonify(resp)


def get_affiliation(email):
    if "wharton" in email:
        return "Wharton"
    elif "seas" in email:
        return "SEAS"
    elif "sas" in email:
        return "SAS"
    else:
        return "Other"


def save_booking(**info):
    item = StudySpacesBooking(**info)

    sqldb.session.add(item)
    sqldb.session.commit()
