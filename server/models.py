import datetime
import uuid

from flask import jsonify, request
from flask_sqlalchemy import SQLAlchemy

sqldb = SQLAlchemy()


def generate_uuid():
    return str(uuid.uuid4())


class Account(sqldb.Model):
    id = sqldb.Column(sqldb.Text, primary_key=True, default=generate_uuid)
    first = sqldb.Column(sqldb.Text, nullable=False)
    last = sqldb.Column(sqldb.Text, nullable=False)
    pennkey = sqldb.Column(sqldb.Text, nullable=False, unique=True)
    email = sqldb.Column(sqldb.Text, nullable=True)
    image_url = sqldb.Column(sqldb.Text, nullable=True)
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())


class School(sqldb.Model):
    id = sqldb.Column(sqldb.Integer, primary_key=True)
    name = sqldb.Column(sqldb.Text, nullable=False)
    code = sqldb.Column(sqldb.Text, nullable=False)


class Degree(sqldb.Model):
    code = sqldb.Column(sqldb.Text, primary_key=True)
    name = sqldb.Column(sqldb.Text, nullable=False)
    school_id = sqldb.Column(sqldb.Text, sqldb.ForeignKey("school.id"), nullable=False)


class Major(sqldb.Model):
    code = sqldb.Column(sqldb.Text, primary_key=True)
    name = sqldb.Column(sqldb.Text, nullable=False)
    degree_code = sqldb.Column(sqldb.Text, sqldb.ForeignKey("degree.code"), nullable=False)


class SchoolMajorAccount(sqldb.Model):
    account_id = sqldb.Column(sqldb.Text, sqldb.ForeignKey("account.id"), primary_key=True)
    school_id = sqldb.Column(sqldb.Integer, sqldb.ForeignKey("school.id"), primary_key=True)
    major = sqldb.Column(sqldb.Integer, sqldb.ForeignKey("major.code"), primary_key=True, nullable=True)
    expected_grad = sqldb.Column(sqldb.Text, nullable=False)


class Course(sqldb.Model):
    id = sqldb.Column(sqldb.Integer, primary_key=True)
    name = sqldb.Column(sqldb.Text, nullable=False)
    code = sqldb.Column(sqldb.Text, nullable=False)
    section = sqldb.Column(sqldb.Text, nullable=False)
    term = sqldb.Column(sqldb.Text, nullable=False)
    weekdays = sqldb.Column(sqldb.Text, nullable=False)
    start = sqldb.Column(sqldb.Text, nullable=False)
    end = sqldb.Column(sqldb.Text, nullable=False)
    building = sqldb.Column(sqldb.Text, nullable=True)
    building_id = sqldb.Column(sqldb.Integer, nullable=True)
    room = sqldb.Column(sqldb.Text, nullable=True)


class CourseInstructor(sqldb.Model):
    course_id = sqldb.Column(sqldb.Integer, sqldb.ForeignKey("course.id"), primary_key=True)
    name = sqldb.Column(sqldb.Text, primary_key=True) 


class CourseAccount(sqldb.Model):
    account_id = sqldb.Column(sqldb.Text, sqldb.ForeignKey("account.id"), primary_key=True)
    course_id = sqldb.Column(sqldb.Integer, sqldb.ForeignKey("course.id"), primary_key=True)


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
    booking_id = sqldb.Column(sqldb.Text, nullable=True)
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
