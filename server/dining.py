from server import app, sqldb
import datetime
import csv
import re
from .base import cached_route
from .penndata import din, dinV2, wharton
from flask import jsonify, request
from .models import User, DiningPreference, Account, DiningBalance, DiningTransaction
from sqlalchemy import func
from bs4 import BeautifulSoup


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
            days = venue.get("dateHours")
            if days:
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


@app.route('/dining/balance/v2', methods=['POST'])
def parse_and_save_dining_balance():
    try:
        account = Account.get_account()
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    html = request.form.get("html")
    if "You are not currently signed up" in html:
        return jsonify({'hasPlan': False, 'balance': None, 'error': None})

    soup = BeautifulSoup(html, "html.parser")
    divs = soup.findAll("div", {"class": "info-column"})
    dollars = None
    swipes = None
    guest_swipes = None
    added_swipes = None
    if len(divs) >= 4:
        for div in divs[:4]:
            if "Dining Dollars" in div.text:
                dollars = float(div.span.text[1:])
            elif "Regular Visits" in div.text:
                swipes = int(div.span.text)
            elif "Guest Visits" in div.text:
                guest_swipes = int(div.span.text)
            elif "Add-on Visits" in div.text: 
                added_swipes = int(div.span.text)
    else:
        return jsonify({"success": False, "error": "Something went wrong parsing HTML."}), 400

    total_swipes = swipes + added_swipes
    dining_balance = DiningBalance(account_id=account.id, dining_dollars=dollars, swipes=total_swipes, guest_swipes=guest_swipes)
    sqldb.session.add(dining_balance)
    sqldb.session.commit()

    balance = {'dollars': dollars, 'swipes': total_swipes, 'guest_swipes': guest_swipes}
    return jsonify({'hasPlan': True, 'balance': balance, 'error': None})


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
        dollars = float(dining_dollars_str)
        swipes = int(swipes_str)
        g_swipes = int(guest_swipes_str)

        dining_balance = DiningBalance(account_id=account.id, dining_dollars=dollars, swipes=swipes, guest_swipes=g_swipes)
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

    if dining_balance:
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
    else:
        return jsonify({'balance': None})


@app.route('/dining/transactions', methods=['POST'])
def save_dining_dollar_transactions():
    try:
        account = Account.get_account()
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    last_transaction = sqldb.session.query(DiningTransaction.date) \
                                    .filter_by(account_id=account.id) \
                                    .order_by(DiningTransaction.date.desc()) \
                                    .first()

    decoded_content = request.form.get("transactions")
    cr = csv.reader(decoded_content.splitlines(), delimiter=',')

    # Create list of rows, remove headers, and reverse so in order of date
    row_list = list(cr)
    row_list.pop(0)
    row_list.reverse()

    for row in row_list:
        if len(row) == 4:
            date = datetime.datetime.strptime(row[0], '%m/%d/%Y %I:%M%p')
            if last_transaction is None or date > last_transaction.date:
                transaction = DiningTransaction(account_id=account.id, date=date, description=row[1], amount=float(row[2]), balance=float(row[3]))
                sqldb.session.add(transaction)
    sqldb.session.commit()

    return jsonify({'success': True, 'error': None})
