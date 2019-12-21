from datetime import datetime

from sqlalchemy import and_, func

from server import sqldb
from server.models import Account, User, StudySpacesBooking
from server.notifications import NotificationToken, send_push_notification


@app.route('/studyspaces/reminders/send', methods=['POST'])
def request_send_reminders():
	send_reminders()


def send_reminders():
	print("Send reminders!")

	minutes = 10
	check_date = datetime.now() + timedelta(minutes=minutes)
	get_gsr = StudySpacesBooking.query \
								.filter(StudySpacesBooking.start <= check_date) \
								.filter(StudySpacesBooking.start > datetime.now()) \
								.filter(StudySpacesBooking.is_cancelled == 0) \
								.subquery()

    get_tokens = NotificationToken.query.filter(NotificationToken.ios_token != None).subquery()

    # TODO: Join subqueries on account ID and send a push notification for each gsr reservation
