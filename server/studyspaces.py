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
    except APIError as e:
        return jsonify({"error": str(e)})

    return jsonify({'result': result})


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
            return jsonify({"error": "Unauthorized: This reservation was booked by someone else."})
        if booking.is_cancelled:
            return jsonify({"error": "This reservation has already been cancelled."})

    if booking_id.isdigit():
        sessionid = request.form.get('sessionid')
        if not sessionid:
            return jsonify({"error": "No session id sent to server."})
        try:
            wharton.delete_booking(sessionid, booking_id)
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
            return jsonify({"error": str(e)})
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

    try:
        lid = int(request.form["lid"])
    except (KeyError, ValueError):
        lid = None

    try:
        user = User.get_user()
        if user and user.email:
            user.email = contact["email"]
            sqldb.session.commit()
        user = user.id
    except ValueError:
        user = None

    resp = studyspaces.book_room(room, start.isoformat(), end.isoformat(), **contact)
    if resp["results"]:
        save_booking(
            lid=lid,
            rid=room,
            email=contact["email"],
            start=start.replace(tzinfo=None),
            end=end.replace(tzinfo=None),
            booking_id=resp.get("booking_id"),
            user=user
        )
    return jsonify(resp)


@app.route('/studyspaces/reservations', methods=['GET'])
def get_reservations():
    """
    Gets a users reservations.
    """

    email = request.args.get('email')
    sessionid = request.args.get('sessionid')
    if not email and not sessionid:
        return jsonify({"error": "A session id or email must be sent to server."})

    libcal_search_span = request.args.get("libcal_search_span")
    if libcal_search_span:
        try:
            libcal_search_span = int(libcal_search_span)
        except ValueError:
            return jsonify({"error": "Search span must be an integer"})
    else:
        libcal_search_span = 3

    reservations = []
    if sessionid:
        try:
            gsr_reservations = wharton.get_reservations(sessionid)

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
                    res["fromDate"] = date_str + "T00:00:00-05:00"
                elif res["startTime"] == "noon":
                    res["fromDate"] = date_str + "T12:00:00-05:00"
                else:
                    start_str = res["startTime"].replace(".", "").upper()
                    try:
                        start_time = datetime.datetime.strptime(start_str, "%I:%M %p")
                    except ValueError:
                        start_time = datetime.datetime.strptime(start_str, "%I %p")
                    start_str = datetime.datetime.strftime(start_time, "%H:%M:%S")
                    res["fromDate"] = "{}T{}-05:00".format(date_str, start_str)

                if res["endTime"] == "midnight":
                    date += datetime.timedelta(days=1)
                    date_str = datetime.datetime.strftime(date, "%Y-%m-%d")
                    res["toDate"] = date_str + "T00:00:00-05:00"
                elif res["endTime"] == "noon":
                    res["toDate"] = date_str + "T12:00:00-05:00"
                else:
                    end_str = res["endTime"].replace(".", "").upper()
                    try:
                        end_time = datetime.datetime.strptime(end_str, "%I:%M %p")
                    except ValueError:
                        end_time = datetime.datetime.strptime(end_str, "%I %p")
                    end_str = datetime.datetime.strftime(end_time, "%H:%M:%S")
                    res["toDate"] = "{}T{}-05:00".format(date_str, end_str)

                del res["date"]
                del res["startTime"]
                del res["endTime"]

            reservations.extend(gsr_reservations)

        except APIError as e:
            return jsonify({"error": str(e)})

    if email:
        try:
            def is_not_cancelled_in_db(booking_id):
                booking = StudySpacesBooking.query.filter_by(booking_id=booking_id).first()
                return not (booking and booking.is_cancelled)

            now = datetime.datetime.now()
            dateFormat = "%Y-%m-%d"
            i = 0
            confirmed_reservations = []
            while len(confirmed_reservations) == 0 and i < libcal_search_span:
                date = now + datetime.timedelta(days=i)
                dateStr = datetime.datetime.strftime(date, dateFormat)
                libcal_reservations = studyspaces.get_reservations(email, dateStr)
                confirmed_reservations = [res for res in libcal_reservations if (res["status"] == "Confirmed"
                    and datetime.datetime.strptime(res["toDate"][:-6], "%Y-%m-%dT%H:%M:%S") >= now)]
                confirmed_reservations = [res for res in confirmed_reservations if is_not_cancelled_in_db(res["bookId"])]
                i += 1

            # Fetch reservations in database that are not being returned by API
            db_bookings = StudySpacesBooking.query.filter_by(email=email)
            db_booking_ids = [str(x.booking_id) for x in db_bookings if x.end and x.end > now and not str(x.booking_id).isdigit() and not x.is_cancelled]
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

        except APIError as e:
            return jsonify({"error": str(e)})

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

    return jsonify({'reservations': reservations})


def save_booking(**info):
    item = StudySpacesBooking(**info)

    sqldb.session.add(item)
    sqldb.session.commit()
