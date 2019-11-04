import datetime
import os

import pytz
from flask import jsonify, request
from penn.base import APIError
from sqlalchemy import and_, func

from server import app, sqldb
from server.account import get_courses_in_N_days, get_todays_courses
from server.calendar3year import pull_todays_calendar
from server.models import Account, DiningPreference, Event, HomeCell, LaundryPreference, StudySpacesBooking, User
from server.news import fetch_frontpage_article
from server.portal.posts import get_posts_for_account
from server.studyspaces.reservations import get_reservations


utc = pytz.timezone('UTC')
eastern = pytz.timezone('US/Eastern')


@app.route('/appversion/iOS', methods=['POST'])
def update_app_version():
    secret = os.environ.get('AUTH_SECRET')
    auth_secret = request.form.get('auth_secret')
    if auth_secret is None:
        return jsonify({'error': 'Auth secret is not provided.'}), 400
    if not auth_secret == secret:
        return jsonify({'error': 'Auth secret is not correct.'}), 400

    version = request.form.get('version')
    if version is None:
        return jsonify({'err': 'No version passed to server'}), 400

    os.environ['APP_VERSION'] = version
    return jsonify({'success': 'App version has been updated to ' + version})


@app.route('/appversion/iOS', methods=['GET'])
def get_app_version():
    version = os.environ.get('APP_VERSION')
    return jsonify({'version': version})


@app.route('/homepage', methods=['GET'])
def get_homepage():
    # Find user in database
    try:
        user = User.get_or_create()
    except ValueError as e:
        response = jsonify({'err': [str(e)]})
        response.status_code = 400
        return response

    try:
        account = Account.get_account()
    except ValueError:
        account = None

    if account and account.email and user.email is None:
        user.email = account.email
        sqldb.session.commit()

    cells = []

    sessionid = request.args.get('sessionid')
    reservations_cell = get_reservations_cell(user, sessionid)
    if reservations_cell:
        cells.append(reservations_cell)

    version = request.args.get('version')

    # if account and account.is_student():
    #     courses = get_courses_cell(account)
    #     if courses:
    #         cells.append(courses)

    laundry = get_top_laundry_cell(user)
    dining = get_dining_cell(user)
    cells.extend([dining, laundry])

    if version and version >= '5.1.1':
        gsr_locations = get_gsr_locations_cell(user, account)
        cells.append(gsr_locations)

    app_version = os.environ.get('APP_VERSION')

    if version and version < app_version:
        update_cell = get_version_cell(version)
        cells.append(update_cell)

    calendar = get_university_event_cell()
    if calendar:
        cells.append(calendar)

    news = get_news_cell()
    if news:
        cells.append(news)

    feature = get_feature_announcement_cell()
    if feature:
        cells.append(feature)

    posts = get_post_cells(account)
    if posts:
        cells.extend(posts)

    cells.sort(key=lambda x: x.weight, reverse=True)

    response = jsonify({'cells': [x.getCell() for x in cells]})
    response.status_code = 200
    return response


def get_dining_cell(user):
    # returns a dining cell
    preferences = sqldb.session.query(DiningPreference.venue_id).filter_by(user_id=user.id)
    venue_ids = [x.venue_id for x in preferences]
    defaults_ids = [593, 1442, 636]
    if len(venue_ids) == 0:
        venue_ids = defaults_ids
    elif len(venue_ids) == 1:
        venue_ids.extend(defaults_ids)
        venue_ids = list(set(venue_ids))[:3]

    info = {'venues': venue_ids}
    return HomeCell('dining', info, 100)


def get_laundry_cells(user):
    # returns a list of laundry cells
    preferences = LaundryPreference.query.filter_by(user_id=user.id)
    room_ids = [x.room_id for x in preferences]

    # If the user has no preferences, select Bishop White
    if not room_ids:
        room_ids.append(0)

    return [HomeCell('laundry', {'room_id': x}) for x in room_ids]


def get_top_laundry_cell(user):
    # returns user's top laundry cell
    top_preference = LaundryPreference.query.filter_by(user_id=user.id).first()
    # If no top choice, select bishop white
    if top_preference:
        return HomeCell('laundry', {'room_id': top_preference.room_id}, 5)
    return HomeCell('laundry', {'room_id': 0}, 5)


def get_gsr_locations_cell(user, account):
    # returns a gsr cell with list of locations
    # if student is a Wharton student, show at the top
    top_gsrs_query = sqldb.session.query(StudySpacesBooking.lid) \
                                  .filter(and_(StudySpacesBooking.user == user.id,
                                               StudySpacesBooking.lid.isnot(None))) \
                                  .group_by(StudySpacesBooking.lid) \
                                  .order_by(func.count(StudySpacesBooking.lid).desc()) \
                                  .limit(2) \
                                  .all()
    preferences = [x for (x,) in top_gsrs_query]

    showHuntsman = account is None or account.email is None or 'wharton' in account.email
    if showHuntsman:
        default_gids = [1, 1086]
        weighting = 300
    else:
        default_gids = [1086, 2587]
        weighting = 10

    # Remove duplicates while retaining relative ordering
    def f7(seq):
        seen = set()
        seen_add = seen.add
        return [x for x in seq if not (x in seen or seen_add(x))]

    gids = f7(preferences + default_gids)[:2]
    return HomeCell('gsr-locations', gids, weighting)


def get_university_event_cell():
    # returns a university notification cell
    calendar = pull_todays_calendar()
    if calendar:
        return HomeCell('calendar', calendar, 40)
    else:
        return None


def get_news_cell():
    # returns a news cell
    article = fetch_frontpage_article()
    if article:
        return HomeCell('news', article, 50)
    else:
        return None


def get_event_cell():
    # return a event cell
    # TODO Fetch most recent, most popular, etc
    event = Event.query.first()
    if event:
        info = {
            'name': event.name,
            'description': event.description,
            'image_url': event.image_url,
            'start_time': utc.localize(event.start_time).astimezone(eastern).isoformat(),
            'end_time': utc.localize(event.end_time).astimezone(eastern).isoformat(),
            'email': event.email,
            'website': event.website,
            'facebook': event.facebook
        }
        return HomeCell('event', info)
    else:
        return None


def get_feature_announcement_cell():
    # returns an announcement for a new Penn Mobile feature
    now = datetime.datetime.now().date()
    start = datetime.date(2019, 4, 12)
    end = datetime.date(2019, 4, 13)
    if now < start or now > end:
        return None

    info = {
        'source': 'Spring Fling',
        'title': 'Tap to view the Fling schedule, performers, and more!',
        'description': None,
        'timestamp': 'Saturday 4/13',
        'image_url': 'ADD IMAGE HERE',
        'feature': 'Spring Fling',
    }
    return HomeCell('feature', info, 2000)


def get_courses_cell(account):
    # return a cell containing today's courses
    courses = get_todays_courses(account)

    # Return today's courses if last course has not yet ended
    now = datetime.datetime.now()
    weekday = int(now.strftime('%w'))
    if courses:
        for course in courses:
            end_time = datetime.datetime.strptime(course['end_time'], '%I:%M %p')
            if now.hour < end_time.hour or (now.hour == end_time.hour and now.minute < end_time.minute):
                return HomeCell('courses', {'weekday': 'Today', 'courses': courses}, 200)
    elif weekday == 6:
        # Return Monday's courses if today is Saturday
        courses = get_courses_in_N_days(account, 2)
        return HomeCell('courses', {'weekday': 'Monday', 'courses': courses}, 30)
    elif weekday != 0:
        # Return empty cell if there are no courses today and today isn't Saturday or Sunday
        return HomeCell('courses', {'weekday': 'Today', 'courses': []}, 30)

    # Return tomorrow's courses if today's last course has ended
    courses = get_courses_in_N_days(account, 1)
    return HomeCell('courses', {'weekday': 'Tomorrow', 'courses': courses}, 30)


def get_reservations_cell(user, sessionid):
    # returns a cell with the user's reservations, weighted extremely high to appear at the top
    # returns None if user has no reservations
    try:
        reservations = get_reservations(user.email, sessionid, 1, 2)
        if reservations:
            return HomeCell('reservations', reservations, 1000)
        else:
            return None
    except APIError:
        return None


def get_post_cells(account):
    posts = get_posts_for_account(account)
    cells = []
    for post in posts:
        cell = HomeCell('post', post, 15000)
        cells.append(cell)
    return cells


def get_version_cell(version):
    return HomeCell('new-version-released', None, 10000)
