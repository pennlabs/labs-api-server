import datetime
import uuid

from flask import request
from flask_sqlalchemy import SQLAlchemy


sqldb = SQLAlchemy()


def generate_uuid():
    return str(uuid.uuid4())


class Account(sqldb.Model):
    id = sqldb.Column(sqldb.VARCHAR(255), primary_key=True, default=generate_uuid)
    first = sqldb.Column(sqldb.Text, nullable=False)
    last = sqldb.Column(sqldb.Text, nullable=False)
    pennkey = sqldb.Column(sqldb.VARCHAR(255), nullable=False, unique=True)
    email = sqldb.Column(sqldb.Text, nullable=True)
    image_url = sqldb.Column(sqldb.Text, nullable=True)
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())

    @staticmethod
    def get_account():
        account_id = request.headers.get('X-Account-ID')
        if not account_id:
            raise ValueError('No account ID passed to the server.')
        account = Account.query.filter_by(id=account_id).first()
        if not account:
            raise ValueError('Unable to authenticate account id.')
        return account

    def is_student(self):
        return sqldb.session.query(SchoolMajorAccount.query.filter_by(account_id=self.id).exists()).scalar()


class School(sqldb.Model):
    id = sqldb.Column(sqldb.Integer, primary_key=True)
    name = sqldb.Column(sqldb.Text, nullable=False)
    code = sqldb.Column(sqldb.Text, nullable=False)


class Degree(sqldb.Model):
    code = sqldb.Column(sqldb.VARCHAR(255), primary_key=True)
    name = sqldb.Column(sqldb.Text, nullable=False)
    school_id = sqldb.Column(sqldb.Integer, sqldb.ForeignKey('school.id'), nullable=False)


class Major(sqldb.Model):
    code = sqldb.Column(sqldb.VARCHAR(255), primary_key=True)
    name = sqldb.Column(sqldb.Text, nullable=False)
    degree_code = sqldb.Column(sqldb.VARCHAR(255), sqldb.ForeignKey('degree.code'), nullable=False)


class SchoolMajorAccount(sqldb.Model):
    account_id = sqldb.Column(sqldb.VARCHAR(255), sqldb.ForeignKey('account.id'), primary_key=True)
    school_id = sqldb.Column(sqldb.Integer, sqldb.ForeignKey('school.id'), primary_key=True)
    major = sqldb.Column(sqldb.VARCHAR(255), sqldb.ForeignKey('major.code'), primary_key=True, nullable=True)
    expected_grad = sqldb.Column(sqldb.Text, nullable=False)


class Course(sqldb.Model):
    id = sqldb.Column(sqldb.Integer, primary_key=True)
    name = sqldb.Column(sqldb.Text, nullable=False)
    dept = sqldb.Column(sqldb.Text, nullable=False)
    code = sqldb.Column(sqldb.Text, nullable=False)
    section = sqldb.Column(sqldb.Text, nullable=False)
    term = sqldb.Column(sqldb.Text, nullable=False)
    weekdays = sqldb.Column(sqldb.Text, nullable=False)
    start_date = sqldb.Column(sqldb.Date, nullable=True)
    end_date = sqldb.Column(sqldb.Date, nullable=True)
    start_time = sqldb.Column(sqldb.Text, nullable=False)
    end_time = sqldb.Column(sqldb.Text, nullable=False)
    building = sqldb.Column(sqldb.Text, nullable=True)
    room = sqldb.Column(sqldb.Text, nullable=True)
    extra_meetings_flag = sqldb.Column(sqldb.Boolean, default=False)


class CourseMeetingTime(sqldb.Model):
    course_id = sqldb.Column(sqldb.Integer, sqldb.ForeignKey('course.id'), primary_key=True)
    weekday = sqldb.Column(sqldb.VARCHAR(3), primary_key=True)
    start_time = sqldb.Column(sqldb.VARCHAR(10), primary_key=True)
    end_time = sqldb.Column(sqldb.Text, nullable=False)
    building = sqldb.Column(sqldb.Text, nullable=True)
    room = sqldb.Column(sqldb.Text, nullable=True)


class CourseInstructor(sqldb.Model):
    course_id = sqldb.Column(sqldb.Integer, sqldb.ForeignKey('course.id'), primary_key=True)
    name = sqldb.Column(sqldb.VARCHAR(255), primary_key=True)


class CourseAccount(sqldb.Model):
    account_id = sqldb.Column(sqldb.VARCHAR(255), sqldb.ForeignKey('account.id'), primary_key=True)
    course_id = sqldb.Column(sqldb.Integer, sqldb.ForeignKey('course.id'), primary_key=True)


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
    user = sqldb.Column(sqldb.Integer, sqldb.ForeignKey('user.id'), nullable=True)
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
            raise ValueError('No device ID passed to the server.')

        user = User.query.filter_by(device_id=device_id).first()
        if user:
            return user

        agent = request.headers.get('User-Agent')
        if any(device in agent.lower() for device in ['iphone', 'ipad']):
            platform = 'ios'
        elif any(device in agent.lower() for device in ['android']):
            platform = 'android'
        else:
            platform = 'unknown'

        user = User(platform=platform, device_id=device_id, email=email)
        sqldb.session.add(user)
        sqldb.session.commit()
        return user

    @staticmethod
    def get_user():
        device_id = request.headers.get('X-Device-ID')
        if not device_id:
            raise ValueError('No device ID passed to the server.')
        user = User.query.filter_by(device_id=device_id).first()
        if not user:
            raise ValueError('Unable to authenticate on the server.')
        return user


class LaundryPreference(sqldb.Model):
    id = sqldb.Column(sqldb.Integer, primary_key=True)
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())
    user_id = sqldb.Column(sqldb.Integer, sqldb.ForeignKey('user.id'), nullable=False)
    room_id = sqldb.Column(sqldb.Integer, nullable=False)


class DiningPreference(sqldb.Model):
    id = sqldb.Column(sqldb.Integer, primary_key=True)
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())
    user_id = sqldb.Column(sqldb.Integer, sqldb.ForeignKey('user.id'), nullable=False)
    venue_id = sqldb.Column(sqldb.Integer, nullable=False)


class DiningBalance(sqldb.Model):
    id = sqldb.Column(sqldb.Integer, primary_key=True)
    account_id = sqldb.Column(sqldb.VARCHAR(255), sqldb.ForeignKey('account.id'))
    dining_dollars = sqldb.Column(sqldb.Float, nullable=False)
    swipes = sqldb.Column(sqldb.Integer, nullable=False)
    guest_swipes = sqldb.Column(sqldb.Integer, nullable=False)
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())


class DiningTransaction(sqldb.Model):
    id = sqldb.Column(sqldb.Integer, primary_key=True)
    account_id = sqldb.Column(sqldb.VARCHAR(255), sqldb.ForeignKey('account.id'))
    date = sqldb.Column(sqldb.DateTime, nullable=False)
    description = sqldb.Column(sqldb.Text, nullable=False)
    amount = sqldb.Column(sqldb.Float, nullable=False)
    balance = sqldb.Column(sqldb.Float, nullable=False)
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())


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


class AnalyticsEvent(sqldb.Model):
    id = sqldb.Column(sqldb.Integer, primary_key=True)
    user = sqldb.Column(sqldb.Integer, sqldb.ForeignKey('user.id'))
    account_id = sqldb.Column(sqldb.VARCHAR(255), sqldb.ForeignKey('account.id'), nullable=True)
    timestamp = sqldb.Column(sqldb.DateTime(3), nullable=False)
    type = sqldb.Column(sqldb.Text, nullable=False)
    index = sqldb.Column(sqldb.Integer, nullable=False)
    post_id = sqldb.Column(sqldb.VARCHAR(255), nullable=True)
    is_interaction = sqldb.Column(sqldb.Boolean, nullable=False)
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())


class PostAccount(sqldb.Model):
    id = sqldb.Column(sqldb.VARCHAR(255), primary_key=True, default=generate_uuid)
    name = sqldb.Column(sqldb.Text, nullable=False)
    email = sqldb.Column(sqldb.VARCHAR(255), nullable=False, unique=True)
    encrypted_password = sqldb.Column(sqldb.VARCHAR(255), nullable=False)
    reset_password_token = sqldb.Column(sqldb.VARCHAR(255), nullable=True, unique=True)
    reset_password_token_sent_at = sqldb.Column(sqldb.DateTime, nullable=True)
    sign_in_count = sqldb.Column(sqldb.Integer, default=1)
    last_sign_in_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())
    updated_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())

    @staticmethod
    def get_account(account_id):
        if not account_id:
            raise ValueError('No account id provided.')

        account = PostAccount.query.filter_by(id=account_id).first()
        if not account:
            raise ValueError('Unable to authenticate account id.')
        return account


class Post(sqldb.Model):
    id = sqldb.Column(sqldb.Integer, primary_key=True)
    account = sqldb.Column(sqldb.VARCHAR(255), sqldb.ForeignKey('post_account.id'), nullable=False)
    source = sqldb.Column(sqldb.Text, nullable=True)
    title = sqldb.Column(sqldb.Text, nullable=True)
    subtitle = sqldb.Column(sqldb.Text, nullable=True)
    time_label = sqldb.Column(sqldb.Text, nullable=True)
    post_url = sqldb.Column(sqldb.Text, nullable=True)
    image_url = sqldb.Column(sqldb.Text, nullable=False)
    image_url_cropped = sqldb.Column(sqldb.Text, nullable=False)
    filters = sqldb.Column(sqldb.Boolean, default=False)
    start_date = sqldb.Column(sqldb.DateTime, nullable=False)
    end_date = sqldb.Column(sqldb.DateTime, nullable=False)
    approved = sqldb.Column(sqldb.Boolean, default=False)
    testers = sqldb.Column(sqldb.Boolean, default=False)
    emails = sqldb.Column(sqldb.Boolean, default=False)
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())

    @staticmethod
    def get_post(post_id):
        if not post_id:
            raise ValueError('No post id provided.')

        account = Post.query.filter_by(id=post_id).first()
        if not account:
            raise ValueError('Unable to authenticate account id.')
        return account


class PostFilter(sqldb.Model):
    post = sqldb.Column(sqldb.Integer, sqldb.ForeignKey('post.id'), primary_key=True)
    type = sqldb.Column(sqldb.VARCHAR(255), primary_key=True)
    filter = sqldb.Column(sqldb.VARCHAR(255), primary_key=True)


class PostStatus(sqldb.Model):
    post = sqldb.Column(sqldb.Integer, sqldb.ForeignKey('post.id'), primary_key=True)
    status = sqldb.Column(sqldb.VARCHAR(255), primary_key=True)
    msg = sqldb.Column(sqldb.VARCHAR(255), nullable=True)
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now(), primary_key=True)


class PostAccountEmail(sqldb.Model):
    account = sqldb.Column(sqldb.VARCHAR(255), sqldb.ForeignKey('post_account.id'), primary_key=True)
    email = sqldb.Column(sqldb.VARCHAR(255), primary_key=True)
    verified = sqldb.Column(sqldb.Boolean, default=False)
    auth_token = sqldb.Column(sqldb.VARCHAR(255), nullable=False)
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())


class PostTester(sqldb.Model):
    post = sqldb.Column(sqldb.Integer, sqldb.ForeignKey('post.id'), primary_key=True)
    email = sqldb.Column(sqldb.VARCHAR(255), primary_key=True)


class PostTargetEmail(sqldb.Model):
    post = sqldb.Column(sqldb.Integer, sqldb.ForeignKey('post.id'), primary_key=True)
    email = sqldb.Column(sqldb.VARCHAR(255), primary_key=True)


class HomeCell(object):
    """A home cell which can be displayed on the home page.

    Usage:

        >>> import HomeCell
        >>> type = 'dining'
        >>> info = { 'venues': [593, 724, 331] }
        >>> weight = 10
        >>> cell = HomeCell(type, info, weight)

    """

    def __init__(self, myType, myInfo=None, myWeight=0):
        self.type = myType
        self.info = myInfo
        self.weight = myWeight

    def getCell(self):
        return {'type': self.type, 'info': self.info}
