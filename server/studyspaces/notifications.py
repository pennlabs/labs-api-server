import math
from datetime import datetime, timedelta

from flask import jsonify, request
from sqlalchemy import and_, not_

from server import app, sqldb
from server.auth import internal_auth
from server.notifications import Notification, NotificationToken, send_push_notification_batch
from server.studyspaces.availability import get_room_name
from server.studyspaces.models import GSRRoomName, StudySpacesBooking


@app.route('/studyspaces/reminders/send', methods=['POST'])
@internal_auth
def request_send_reminders():
    isDev = True if request.form.get("dev") else False
    send_reminders(isDev)
    return jsonify({'result': 'success'})


def send_reminders(isDev=False):
    # Query logic
    # Get bookings that meet the following criteria:
    # 1) Start within the next 10 minutes
    # 2) Booked more than 30 minutes before the start time
    # 3) Have not been cancelled
    # 4) Have not been sent a reminder yet
    # 5) Have an associated account with an iOS push notification token

    now = datetime.now()
    check_start_date = now + timedelta(minutes=30)
    get_gsr = StudySpacesBooking.query \
                                .filter(StudySpacesBooking.start <= check_start_date) \
                                .filter(StudySpacesBooking.start > now) \
                                .filter(StudySpacesBooking.date < StudySpacesBooking.start - timedelta(minutes=30)) \
                                .filter(not_(StudySpacesBooking.is_cancelled)) \
                                .filter(not_(StudySpacesBooking.reminder_sent)) \
                                .filter(StudySpacesBooking.account is not None) \
                                .subquery()

    get_tokens = NotificationToken.query.filter(NotificationToken.ios_token is not None).subquery()

    join_qry = sqldb.session.query(get_gsr.c.id, get_gsr.c.lid, get_gsr.c.rid, GSRRoomName.name,
                                   get_gsr.c.start, get_tokens.c.ios_token) \
                            .select_from(get_gsr) \
                            .join(get_tokens, get_gsr.c.account == get_tokens.c.account) \
                            .join(GSRRoomName, and_(get_gsr.c.lid == GSRRoomName.lid,
                                                    get_gsr.c.rid == GSRRoomName.rid), isouter=True) \
                            .all()

    booking_ids = []
    notifications = []
    for bid, lid, rid, name, start, token in join_qry:
        minutes_to_start = int(math.ceil((start - now).seconds / 60))
        title = 'Upcoming reservation'
        if not name:
            # Fetch name from API if it does not already exist in the DB
            name = get_room_name(lid, rid)
        if name:
            body = 'You have reserved {} starting in {} minutes'.format(name, minutes_to_start)
        else:
            body = 'You have a reservation starting in {} minutes'.format(minutes_to_start)
        alert = {'title': title, 'body': body}
        notification = Notification(token=token, alert=alert)
        notifications.append(notification)
        booking_ids.append(bid)

    if notifications:
        send_push_notification_batch(notifications, isDev)

    # Flag each booking as SENT so that a duplicate notification is not accidentally sent
    bookings = StudySpacesBooking.query.filter(StudySpacesBooking.id.in_(tuple(booking_ids))).all()
    for booking in bookings:
        booking.reminder_sent = True
    sqldb.session.commit()
