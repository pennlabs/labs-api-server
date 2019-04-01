import os
import datetime
import requests

from flask import jsonify, request
from dateutil.parser import parse

from server import app, db, sqldb
from penn.base import APIError
from .models import StudySpacesBooking, User
from .penndata import studyspaces, wharton
from .base import cached_route


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


@app.route('/studyspaces/gsr', methods=['GET'])
def get_wharton_gsrs_temp_route():
    """ Temporary endpoint to allow non-authenticated users to access the list of GSRs. """
    date = request.args.get('date')
    try:
        data = wharton.get_wharton_gsrs(get_wharton_sessionid(public=True), date)
        save_wharton_sessionid()
        return jsonify(data)
    except APIError as error:
        return jsonify({'error': str(error)}), 400


@app.route('/studyspaces/gsr/reservations', methods=['GET'])
def get_wharton_gsr_reservations():
    """
    Returns JSON containing a list of Wharton GSR reservations.
    """

    sessionid = get_wharton_sessionid()

    if not sessionid:
        return jsonify({'error': 'No Session ID provided.'})

    try:
        reservations = wharton.get_reservations(sessionid)
        save_wharton_sessionid()
        return jsonify({'reservations': reservations})
    except APIError as e:
        return jsonify({"error": str(e)}), 400


@app.route('/studyspaces/gsr/delete', methods=['POST'])
def delete_wharton_gsr_reservation():
    """
    Deletes a Wharton GSR reservation
    """
    booking = request.form.get('booking')
    sessionid = request.form.get('sessionid')
    if not booking:
        return jsonify({"error": "No booking sent to server."})
    if not sessionid:
        return jsonify({"error": "No session id sent to server."})

    try:
        result = wharton.delete_booking(sessionid, booking)
        save_wharton_sessionid()
        return jsonify({'result': result})
    except APIError as e:
        return jsonify({"error": str(e)}), 400


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


@app.route('/studyspaces/cancel', methods=['POST'])
def cancel_room():
    """
    Cancels a booked room.
    """
    try:
        user = User.get_user()
    except ValueError as err:
        return jsonify({"error": str(err)})

    booking_id = request.form.get("booking_id")
    if not booking_id:
        return jsonify({"error": "No booking id sent to server!"})
    if "," in booking_id:
        return jsonify({"error": "Only one booking may be cancelled at a time."})

    booking = StudySpacesBooking.query.filter_by(booking_id=booking_id).first()
    if booking:
        if (booking.user is not None) and (booking.user != user.id):
            return jsonify({"error": "Unauthorized: This reservation was booked by someone else."}), 400
        if booking.is_cancelled:
            return jsonify({"error": "This reservation has already been cancelled."}), 400

    if booking_id.isdigit():
        sessionid = request.form.get("sessionid")
        if not sessionid:
            return jsonify({"error": "No session id sent to server."}), 400
        try:
            wharton.delete_booking(sessionid, booking_id)
            save_wharton_sessionid()
            if booking:
                booking.is_cancelled = True
                sqldb.session.commit()
            else:
                save_booking(
                    lid=1,
                    email=user.email,
                    booking_id=booking_id,
                    is_cancelled=True,
                    user=user.id
                )
            return jsonify({'result': [{"booking_id": booking_id, "cancelled": True}]})
        except APIError as e:
            return jsonify({"error": str(e)}), 400
    else:
        resp = studyspaces.cancel_room(booking_id)
        if "error" not in resp:
            if booking:
                booking.is_cancelled = True
                sqldb.session.commit()
            else:
                save_booking(
                    email=user.email,
                    booking_id=booking_id,
                    is_cancelled=True,
                    user=user.id
                )
        return jsonify({'result': resp})


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


@app.route('/studyspaces/reservations', methods=['GET'])
def get_reservations_endpoint():
    """
    Gets a users reservations.
    """

    email = request.args.get('email')
    sessionid = request.args.get('sessionid')
    if not email and not sessionid:
        return jsonify({"error": "A session id or email must be sent to server."}), 400

    libcal_search_span = request.args.get("libcal_search_span")
    if libcal_search_span:
        try:
            libcal_search_span = int(libcal_search_span)
        except ValueError:
            return jsonify({"error": "Search span must be an integer."}), 400
    else:
        libcal_search_span = 3

    try:
        reservations = get_reservations(email, sessionid, libcal_search_span)
        return jsonify({'reservations': reservations})
    except APIError as e:
        return jsonify({"error": str(e)}), 400


def get_reservations(email, sessionid, libcal_search_span, timeout=20):
    reservations = []
    if sessionid:
        try:
            gsr_reservations = wharton.get_reservations(sessionid, timeout)
            timezone = wharton.get_dst_gmt_timezone()

            for res in gsr_reservations:
                res["service"] = "wharton"
                res["booking_id"] = str(res["booking_id"])
                res["name"] = res["location"]
                res["gid"] = 1
                res["lid"] = 1
                res["info"] = None
                del res["location"]

                date = datetime.datetime.strptime(res["date"], "%b %d, %Y")
                date_str = datetime.datetime.strftime(date, "%Y-%m-%d")

                if res["startTime"] == "midnight":
                    res["fromDate"] = date_str + "T00:00:00-{}".format(timezone)
                elif res["startTime"] == "noon":
                    res["fromDate"] = date_str + "T12:00:00-{}".format(timezone)
                else:
                    start_str = res["startTime"].replace(".", "").upper()
                    try:
                        start_time = datetime.datetime.strptime(start_str, "%I:%M %p")
                    except ValueError:
                        start_time = datetime.datetime.strptime(start_str, "%I %p")
                    start_str = datetime.datetime.strftime(start_time, "%H:%M:%S")
                    res["fromDate"] = "{}T{}-{}".format(date_str, start_str, timezone)

                if res["endTime"] == "midnight":
                    date += datetime.timedelta(days=1)
                    date_str = datetime.datetime.strftime(date, "%Y-%m-%d")
                    res["toDate"] = date_str + "T00:00:00-{}".format(timezone)
                elif res["endTime"] == "noon":
                    res["toDate"] = date_str + "T12:00:00-{}".format(timezone)
                else:
                    end_str = res["endTime"].replace(".", "").upper()
                    try:
                        end_time = datetime.datetime.strptime(end_str, "%I:%M %p")
                    except ValueError:
                        end_time = datetime.datetime.strptime(end_str, "%I %p")
                    end_str = datetime.datetime.strftime(end_time, "%H:%M:%S")
                    res["toDate"] = "{}T{}-{}".format(date_str, end_str, timezone)

                del res["date"]
                del res["startTime"]
                del res["endTime"]

            reservations.extend(gsr_reservations)

        except APIError as e:
            pass

    if email:
        confirmed_reservations = []
        try:
            def is_not_cancelled_in_db(booking_id):
                booking = StudySpacesBooking.query.filter_by(booking_id=booking_id).first()
                return not (booking and booking.is_cancelled)

            now = datetime.datetime.now()
            dateFormat = "%Y-%m-%d"
            i = 0
            while len(confirmed_reservations) == 0 and i < libcal_search_span:
                date = now + datetime.timedelta(days=i)
                dateStr = datetime.datetime.strftime(date, dateFormat)
                libcal_reservations = studyspaces.get_reservations(email, dateStr, timeout)
                confirmed_reservations = [res for res in libcal_reservations if (res["status"] == "Confirmed"
                                          and datetime.datetime.strptime(res["toDate"][:-6], "%Y-%m-%dT%H:%M:%S") >= now)]
                confirmed_reservations = [res for res in confirmed_reservations if is_not_cancelled_in_db(res["bookId"])]
                i += 1

        except APIError as e:
            pass

        # Fetch reservations in database that are not being returned by API
        db_bookings = StudySpacesBooking.query.filter_by(email=email)
        db_booking_ids = [str(x.booking_id) for x in db_bookings if x.end
                          and x.end > now
                          and not str(x.booking_id).isdigit()
                          and not x.is_cancelled]
        reservation_ids = [x["bookId"] for x in confirmed_reservations]
        missing_booking_ids = list(set(db_booking_ids) - set(reservation_ids))
        if missing_booking_ids:
            missing_bookings_str = ",".join(missing_booking_ids)
            missing_reservations = studyspaces.get_reservations_for_booking_ids(missing_bookings_str)
            confirmed_missing_reservations = [res for res in missing_reservations if res["status"] == "Confirmed"]
            confirmed_reservations.extend(confirmed_missing_reservations)

        for res in confirmed_reservations:
            res["service"] = "libcal"
            res["booking_id"] = res["bookId"]
            res["room_id"] = res["eid"]
            res["gid"] = res["cid"]
            del res["bookId"]
            del res["eid"]
            del res["cid"]
            del res["status"]
            del res["email"]
            del res["firstName"]
            del res["lastName"]

        room_ids = ",".join(list(set([str(x["room_id"]) for x in confirmed_reservations])))
        if room_ids:
            rooms = studyspaces.get_room_info(room_ids)
            for room in rooms:
                room["thumbnail"] = room["image"]
                del room["image"]
                del room["formid"]

            for res in confirmed_reservations:
                room = [x for x in rooms if x["id"] == res["room_id"]][0]
                res["name"] = room["name"]
                res["info"] = room
                del res["room_id"]
            reservations.extend(confirmed_reservations)

    return reservations


def save_booking(**info):
    item = StudySpacesBooking(**info)

    sqldb.session.add(item)
    sqldb.session.commit()
