from datetime import datetime, timedelta

from flask import jsonify
from sqlalchemy import and_, func

from server import app, sqldb
from server.models import Account, User
from server.notifications import NotificationToken, send_push_notification
from server.studyspaces.models import StudySpacesBooking


@app.route('/studyspaces/reminders/send', methods=['POST'])
def request_send_reminders():
    send_reminders()
    return jsonify({'result': 'success'})


def send_reminders():
    # Send reminder notification 10 minutes before booking starts
    # Do not send reminder notifications for reservations booked with 30 minutes of start time

    check_start_date = datetime.now() + timedelta(minutes=20)
    get_gsr = StudySpacesBooking.query \
                                .filter(StudySpacesBooking.start <= check_start_date) \
                                .filter(StudySpacesBooking.start > datetime.now()) \
                                .filter(StudySpacesBooking.date < StudySpacesBooking.start - timedelta(minutes=30)) \
                                .filter(StudySpacesBooking.is_cancelled == 0) \
                                .filter(StudySpacesBooking.account != None) \
                                .subquery()

    get_tokens = NotificationToken.query.filter(NotificationToken.ios_token != None).subquery()

    # TODO: Join subqueries on account ID and send a push notification for each gsr reservation
    join_qry = sqldb.session.query(get_gsr.c.lid, get_gsr.c.rid, get_gsr.c.start, get_tokens.c.ios_token) \
                            .select_from(get_gsr) \
                            .join(get_tokens, get_gsr.c.account == get_tokens.c.account) \
                            .all()

    for lid, rid, start, token in join_qry:
        title = 'Upcoming Reservation'
        body = 'You have a reservation soon!'
        send_push_notification(token, title, body, True)
