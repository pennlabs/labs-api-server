from server import app, sqldb
import datetime
from .base import cached_route
from .penndata import din, dinV2, wharton
from flask import jsonify, request
from .models import User, DiningPreference, Account, DiningBalance
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
        json = din.venues()['result_data']
        venues = json["document"]["venue"]
        for venue in venues:
            days = venue["dateHours"]
            for day in days:
                meals = day["meal"]
                new_meals = []
                for meal in meals:
                    meal_type = meal["type"]
                    if "Light" not in meal_type:
                        new_meals.append(meal)
                day["meal"] = new_meals
        return json

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

    # delete old preferences for user
    DiningPreference.query.filter_by(user_id=user.id).delete()

    if venues:
        venue_ids = [int(x) for x in venues.split(",")]

        for venue_id in venue_ids:
            dining_preference = DiningPreference(user_id=user.id, venue_id=venue_id)
            sqldb.session.add(dining_preference)
    sqldb.session.commit()

    return jsonify({'success': True, 'error': None})


@app.route('/dining/preferences', methods=['GET'])
def get_dining_preferences():
    try:
        user = User.get_or_create()
    except ValueError:
        return jsonify({'preferences': []})

    preferences = sqldb.session.query(DiningPreference.venue_id, func.count(DiningPreference.venue_id)) \
                               .filter_by(user_id=user.id).group_by(DiningPreference.venue_id).all()
    preference_arr = [{'venue_id': x[0], 'count': x[1]} for x in preferences]
    return jsonify({'preferences': preference_arr})


@app.route('/dining/balance', methods=['POST'])
def save_dining_balance():
    try:
        account = Account.get_account()
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    dining_dollars_str = request.form.get('dining_dollars')
    swipes_str = request.form.get('swipes')
    guest_swipes_str = request.form.get('guest_swipes')

    if dining_dollars_str and swipes_str and guest_swipes_str:
        dining_dollars = float(dining_dollars_str)
        swipes = int(swipes_str)
        guest_swipes = int(guest_swipes_str)

        dining_balance = DiningBalance(account_id=account.id, dining_dollars=dining_dollars, swipes=swipes, 
            guest_swipes=guest_swipes)
        sqldb.session.add(dining_balance)
        sqldb.session.commit()

        return jsonify({'success': True, 'error': None})
    else:
        return jsonify({"success": False, "error": "Field missing"}), 400


@app.route('/dining/balance', methods=['GET'])
def get_dining_balance():
    try:
        account = Account.get_account()
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    dining_balance = DiningBalance.query.filter_by(account_id=account.id) \
        .order_by(DiningBalance.created_at.desc()).first()

    dining_dollars = dining_balance.dining_dollars
    swipes = dining_balance.swipes
    guest_swipes = dining_balance.guest_swipes
    created_at = dining_balance.created_at
    timestamp = created_at.strftime("%Y-%m-%dT%H:%M:%S") + "-{}".format(wharton.get_dst_gmt_timezone())

    return jsonify({'balance': {
            'dining_dollars': dining_dollars,
            'swipes': swipes,
            'guest_swipes': guest_swipes,
            'timestamp': timestamp
        }})


