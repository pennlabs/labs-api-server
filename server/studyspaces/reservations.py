import datetime

from flask import jsonify, request
from penn.base import APIError

from server import app
from server.models import StudySpacesBooking
from server.penndata import studyspaces, wharton


@app.route('/studyspaces/reservations', methods=['GET'])
def get_reservations_endpoint():
    """
    Gets a users reservations.
    """

    email = request.args.get('email')
    sessionid = request.args.get('sessionid')
    if not email and not sessionid:
        return jsonify({'error': 'A session id or email must be sent to server.'}), 400

    libcal_search_span = request.args.get('libcal_search_span')
    if libcal_search_span:
        try:
            libcal_search_span = int(libcal_search_span)
        except ValueError:
            return jsonify({'error': 'Search span must be an integer.'}), 400
    else:
        libcal_search_span = 3

    try:
        reservations = get_reservations(email, sessionid, libcal_search_span)
        return jsonify({'reservations': reservations})
    except APIError as e:
        return jsonify({'error': str(e)}), 400


def get_reservations(email, sessionid, libcal_search_span, timeout=20):
    reservations = []
    if sessionid:
        try:
            gsr_reservations = wharton.get_reservations(sessionid, timeout)
            timezone = wharton.get_dst_gmt_timezone()

            for res in gsr_reservations:
                res['service'] = 'wharton'
                res['booking_id'] = str(res['booking_id'])
                res['name'] = res['location']
                res['gid'] = 1
                res['lid'] = 1
                res['info'] = None
                del res['location']

                date = datetime.datetime.strptime(res['date'], '%b %d, %Y')
                date_str = datetime.datetime.strftime(date, '%Y-%m-%d')

                if res['startTime'] == 'midnight':
                    res['fromDate'] = date_str + 'T00:00:00-{}'.format(timezone)
                elif res['startTime'] == 'noon':
                    res['fromDate'] = date_str + 'T12:00:00-{}'.format(timezone)
                else:
                    start_str = res['startTime'].replace('.', '').upper()
                    try:
                        start_time = datetime.datetime.strptime(start_str, '%I:%M %p')
                    except ValueError:
                        start_time = datetime.datetime.strptime(start_str, '%I %p')
                    start_str = datetime.datetime.strftime(start_time, '%H:%M:%S')
                    res['fromDate'] = '{}T{}-{}'.format(date_str, start_str, timezone)

                if res['endTime'] == 'midnight':
                    date += datetime.timedelta(days=1)
                    date_str = datetime.datetime.strftime(date, '%Y-%m-%d')
                    res['toDate'] = date_str + 'T00:00:00-{}'.format(timezone)
                elif res['endTime'] == 'noon':
                    res['toDate'] = date_str + 'T12:00:00-{}'.format(timezone)
                else:
                    end_str = res['endTime'].replace('.', '').upper()
                    try:
                        end_time = datetime.datetime.strptime(end_str, '%I:%M %p')
                    except ValueError:
                        end_time = datetime.datetime.strptime(end_str, '%I %p')
                    end_str = datetime.datetime.strftime(end_time, '%H:%M:%S')
                    res['toDate'] = '{}T{}-{}'.format(date_str, end_str, timezone)

                del res['date']
                del res['startTime']
                del res['endTime']

            reservations.extend(gsr_reservations)

        except APIError:
            pass

    if email:
        confirmed_reservations = []
        try:
            def is_not_cancelled_in_db(booking_id):
                booking = StudySpacesBooking.query.filter_by(booking_id=booking_id).first()
                return not (booking and booking.is_cancelled)

            now = datetime.datetime.now()
            dateFormat = '%Y-%m-%d'
            i = 0
            while len(confirmed_reservations) == 0 and i < libcal_search_span:
                date = now + datetime.timedelta(days=i)
                dateStr = datetime.datetime.strftime(date, dateFormat)
                libcal_reservations = studyspaces.get_reservations(email, dateStr, timeout)
                confirmed_reservations = [res for res in libcal_reservations if (type(res) == dict
                                          and res['status'] == 'Confirmed'
                                          and datetime.datetime.strptime(res['toDate'][:-6], '%Y-%m-%dT%H:%M:%S')
                                          >= now)]
                confirmed_reservations = [res for res in confirmed_reservations
                                          if is_not_cancelled_in_db(res['bookId'])]
                i += 1

        except APIError:
            pass

        # Fetch reservations in database that are not being returned by API
        db_bookings = StudySpacesBooking.query.filter_by(email=email)
        db_booking_ids = [str(x.booking_id) for x in db_bookings if x.end
                          and x.end > now
                          and not str(x.booking_id).isdigit()
                          and not x.is_cancelled]
        reservation_ids = [x['bookId'] for x in confirmed_reservations]
        missing_booking_ids = list(set(db_booking_ids) - set(reservation_ids))
        if missing_booking_ids:
            missing_bookings_str = ','.join(missing_booking_ids)
            missing_reservations = studyspaces.get_reservations_for_booking_ids(missing_bookings_str)
            confirmed_missing_reservations = [res for res in missing_reservations if res['status'] == 'Confirmed']
            confirmed_reservations.extend(confirmed_missing_reservations)

        for res in confirmed_reservations:
            res['service'] = 'libcal'
            res['booking_id'] = res['bookId']
            res['room_id'] = res['eid']
            res['gid'] = res['cid']
            del res['bookId']
            del res['eid']
            del res['cid']
            del res['status']
            del res['email']
            del res['firstName']
            del res['lastName']

        room_ids = ','.join(list(set([str(x['room_id']) for x in confirmed_reservations])))
        if room_ids:
            rooms = studyspaces.get_room_info(room_ids)
            for room in rooms:
                room['thumbnail'] = room['image']
                del room['image']
                del room['formid']

            for res in confirmed_reservations:
                room = [x for x in rooms if x['id'] == res['room_id']][0]
                res['name'] = room['name']
                res['info'] = room
                del res['room_id']
            reservations.extend(confirmed_reservations)

    return reservations
