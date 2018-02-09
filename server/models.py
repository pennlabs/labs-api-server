import datetime

from flask_sqlalchemy import SQLAlchemy

sqldb = SQLAlchemy()


class LaundrySnapshot(sqldb.Model):
    id = sqldb.Column(sqldb.Integer, primary_key=True)
    date = sqldb.Column(sqldb.Date, nullable=False, index=True)
    time = sqldb.Column(sqldb.Integer, nullable=False)
    room = sqldb.Column(sqldb.Integer, nullable=False)
    washers = sqldb.Column(sqldb.Integer, nullable=False)
    dryers = sqldb.Column(sqldb.Integer, nullable=False)
    total_washers = sqldb.Column(sqldb.Integer, nullable=False)
    total_dryers = sqldb.Column(sqldb.Integer, nullable=False)


class StudySpacesBooking(sqldb.Model):
    id = sqldb.Column(sqldb.Integer, primary_key=True)
    date = sqldb.Column(sqldb.DateTime, default=datetime.datetime.utcnow)
    lid = sqldb.Column(sqldb.Integer, nullable=False)
    rid = sqldb.Column(sqldb.Integer, nullable=False)
    email = sqldb.Column(sqldb.Text, nullable=False)
    start = sqldb.Column(sqldb.DateTime, nullable=False)
    end = sqldb.Column(sqldb.DateTime, nullable=False)
