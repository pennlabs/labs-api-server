import datetime

from server import sqldb


class StudySpacesBooking(sqldb.Model):
    id = sqldb.Column(sqldb.Integer, primary_key=True)
    account = sqldb.Column(sqldb.VARCHAR(255), sqldb.ForeignKey('account.id'), nullable=True)
    user = sqldb.Column(sqldb.Integer, sqldb.ForeignKey('user.id'), nullable=True)
    booking_id = sqldb.Column(sqldb.Text, nullable=True)
    date = sqldb.Column(sqldb.DateTime, default=datetime.datetime.now)
    lid = sqldb.Column(sqldb.Integer, nullable=True)
    rid = sqldb.Column(sqldb.Integer, nullable=True)
    email = sqldb.Column(sqldb.Text, nullable=True)
    start = sqldb.Column(sqldb.DateTime, nullable=True)
    end = sqldb.Column(sqldb.DateTime, nullable=True)
    is_cancelled = sqldb.Column(sqldb.Boolean, default=False)
