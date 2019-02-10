from server import app, sqldb
import datetime
from .base import cached_route
from .penndata import din, dinV2
from flask import jsonify, request
from .models import User, DiningPreference
from sqlalchemy import func


@app.route('/dining/v2/venues', methods=['GET'])
def retrieve_venues_v2():
    def get_data():
        return dinV2.venues()['result_data']

    now = datetime.datetime.today()
    daysTillWeek = 6 - now.weekday()
    td = datetime.timedelta(days=daysTillWeek)
    return cached_route('dining:v2:venues', td, get_data)


@app.route('/dining/v2/menu/<venue_id>/<date>', methods=['GET'])
def retrieve_menu_v2(venue_id, date):
    def get_data():
        return dinV2.menu(venue_id, date)['result_data']

    now = datetime.datetime.today()
    daysTillWeek = 6 - now.weekday()
    td = datetime.timedelta(days=daysTillWeek)
    return cached_route('dining:v2:menu:%s:%s' % (venue_id, date), td,
                        get_data)


@app.route('/dining/v2/item/<item_id>', methods=['GET'])
def retrieve_item_v2(item_id):
    def get_data():
        return dinV2.item(item_id)['result_data']

    now = datetime.datetime.today()
    daysTillWeek = 6 - now.weekday()
    td = datetime.timedelta(days=daysTillWeek)
    return cached_route('dining:v2:item:%s' % item_id, td, get_data)


@app.route('/dining/venues', methods=['GET'])
def retrieve_venues():
    def get_data():
        return din.venues()['result_data']

    now = datetime.datetime.today()
    daysTillWeek = 6 - now.weekday()
    td = datetime.timedelta(days=daysTillWeek)
    return cached_route('dining:venues', td, get_data)


@app.route('/dining/hours/<venue_id>', methods=['GET'])
def retrieve_hours(venue_id):
    def get_data():
        return dinV2.hours(venue_id)['result_data']

    now = datetime.datetime.today()
    daysTillWeek = 6 - now.weekday()
    td = datetime.timedelta(days=daysTillWeek)
    return cached_route('dining:v2:hours:%s' % venue_id, td, get_data)


@app.route('/dining/weekly_menu/<venue_id>', methods=['GET'])
def retrieve_weekly_menu(venue_id):
    now = datetime.datetime.today()
    daysTillWeek = 6 - now.weekday()
    td = datetime.timedelta(days=daysTillWeek)

    def get_data():
        menu = din.menu_weekly(venue_id)
        return menu["result_data"]

    return cached_route('dining:venues:weekly:%s' % venue_id, td, get_data)


@app.route('/dining/daily_menu/<venue_id>', methods=['GET'])
def retrieve_daily_menu(venue_id):
    now = datetime.datetime.today()
    end_time = datetime.datetime(now.year, now.month,
                                 now.day) + datetime.timedelta(hours=4)

    def get_data():
        return din.menu_daily(venue_id)["result_data"]

    return cached_route('dining:venues:daily:%s' % venue_id, end_time - now,
                        get_data)


@app.route('/dining/preferences', methods=['POST'])
def save_dining_preferences():
    try:
        user = User.get_or_create()
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)})

    venues = request.form.get('venues')

    if venues is None:
        return jsonify({'success': False, 'error': 'Venue form missing.'})

    # delete old preferences for user
    DiningPreference.query.filter_by(user_id=user.id).delete()

    if venues:
        venue_ids = [int(x) for x in venues.split(",")]

        for venue_id in venue_ids:
            dining_preference = DiningPreference(user_id=user.id, venue_id=venue_id)
            sqldb.session.add(dining_preference)
    sqldb.session.commit()

    return jsonify({'success': True, 'error': None})
