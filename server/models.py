import datetime

from flask import jsonify, request
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
    user = sqldb.Column(sqldb.Integer, sqldb.ForeignKey("user.id"), nullable=True)
    booking_id = sqldb.Column(sqldb.Text)
    date = sqldb.Column(sqldb.DateTime, default=datetime.datetime.now)
    lid = sqldb.Column(sqldb.Integer, nullable=True) 
    rid = sqldb.Column(sqldb.Integer, nullable=True)
    email = sqldb.Column(sqldb.Text, nullable=True)
    start = sqldb.Column(sqldb.DateTime, nullable=True)
    end = sqldb.Column(sqldb.DateTime, nullable=True)
    is_cancelled = sqldb.Column(sqldb.Boolean, default=False)


class User(sqldb.Model):
    id = sqldb.Column(sqldb.Integer, primary_key=True)
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())
    platform = sqldb.Column(sqldb.Text, nullable=False)
    device_id = sqldb.Column(sqldb.Text, nullable=False)
    email = sqldb.Column(sqldb.Text, nullable=True)

    @staticmethod
    def get_or_create(device_id=None, platform=None, email=None):
        device_id = device_id or request.headers.get('X-Device-ID')
        if not device_id:
            raise ValueError("No device ID passed to the server.")

        user = User.query.filter_by(device_id=device_id).first()
        if user:
            return user

        agent = request.headers.get('User-Agent')
        if any(device in agent.lower() for device in ["iphone", "ipad"]):
            platform = "ios"
        elif any(device in agent.lower() for device in ["android"]):
            platform = "android"
        else:
            platform = "unknown"

        user = User(platform=platform, device_id=device_id, email=email)
        sqldb.session.add(user)
        sqldb.session.commit()
        return user

    @staticmethod
    def get_user():
        device_id = request.headers.get('X-Device-ID')
        if not device_id:
            raise ValueError("No device ID passed to the server.")
        user = User.query.filter_by(device_id=device_id).first()
        if not user:
            raise ValueError("Unable to authenticate on the server.")
        return user

    @staticmethod
    def create_user():
        device_id = request.form.get('device_id')
        if not device_id:
            raise ValueError("No device ID passed to the server.")
        user = User.query.filter_by(device_id=device_id).first()
        if user:
            return

        agent = request.headers.get('User-Agent')
        if any(device in agent.lower() for device in ["iphone", "ipad"]):
            platform = "ios"
        elif any(device in agent.lower() for device in ["android"]):
            platform = "android"
        else:
            platform = "unknown"
        user = User(platform=platform, device_id=device_id)
        sqldb.session.add(user)
        sqldb.session.commit()


class LaundryPreference(sqldb.Model):
    id = sqldb.Column(sqldb.Integer, primary_key=True)
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())
    user_id = sqldb.Column(sqldb.Integer, sqldb.ForeignKey("user.id"), nullable=False)
    room_id = sqldb.Column(sqldb.Integer, nullable=False)


class DiningPreference(sqldb.Model):
    id = sqldb.Column(sqldb.Integer, primary_key=True)
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())
    user_id = sqldb.Column(sqldb.Integer, sqldb.ForeignKey("user.id"), nullable=False)
    venue_id = sqldb.Column(sqldb.Integer, nullable=False)


class Event(sqldb.Model):
    id = sqldb.Column(sqldb.Integer, primary_key=True)
    type = sqldb.Column(sqldb.Text, nullable=False)
    name = sqldb.Column(sqldb.Text, nullable=False)
    description = sqldb.Column(sqldb.Text, nullable=False)
    image_url = sqldb.Column(sqldb.Text, nullable=False)
    start_time = sqldb.Column(sqldb.DateTime, nullable=False)
    end_time = sqldb.Column(sqldb.DateTime, nullable=False)
    email = sqldb.Column(sqldb.String(255), nullable=False)
    website = sqldb.Column(sqldb.String(255))
    facebook = sqldb.Column(sqldb.String(255))


class HomeCellOrder(sqldb.Model):
    id = sqldb.Column(sqldb.Integer, primary_key=True)
    cell_type = sqldb.Column(sqldb.Text, nullable=False)


class HomeCell(object):
    """A home cell which can be displayed on the home page.

    Usage:

        >>> import HomeCell
        >>> type = "dining"
        >>> info = { "venues": [593, 724, 331] }
        >>> cell = HomeCell(type, info)

    """

    def __init__(self, myType, myInfo=None):
        self.type = myType
        self.info = myInfo

    def getCell(self):
        return {"type": self.type, "info": self.info}
