from datetime import datetime

from pytz import timezone

from server import sqldb


def get_est_date():
    est = timezone('EST')
    return datetime.now(est).replace(tzinfo=None)


class StudySpacesBooking(sqldb.Model):
    id = sqldb.Column(sqldb.Integer, primary_key=True)
    account = sqldb.Column(sqldb.VARCHAR(255), sqldb.ForeignKey('account.id'), nullable=True)
    user = sqldb.Column(sqldb.Integer, sqldb.ForeignKey('user.id'), nullable=True)
    booking_id = sqldb.Column(sqldb.Text, nullable=True)
    date = sqldb.Column(sqldb.DateTime, default=get_est_date)
    lid = sqldb.Column(sqldb.Integer, nullable=True)
    rid = sqldb.Column(sqldb.Integer, nullable=True)
    email = sqldb.Column(sqldb.Text, nullable=True)
    start = sqldb.Column(sqldb.DateTime, nullable=True)
    end = sqldb.Column(sqldb.DateTime, nullable=True)
    is_cancelled = sqldb.Column(sqldb.Boolean, default=False)
    reminder_sent = sqldb.Column(sqldb.Boolean, default=False)


class GSRRoomName(sqldb.Model):
    lid = sqldb.Column(sqldb.Integer, primary_key=True)
    gid = sqldb.Column(sqldb.Integer, primary_key=True)
    rid = sqldb.Column(sqldb.Integer, primary_key=True)
    name = sqldb.Column(sqldb.VARCHAR(255))
    image_url = sqldb.Column(sqldb.VARCHAR(255), nullable=True)
