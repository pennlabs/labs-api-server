import datetime

from server import app, db
from server.base import cached_route
from server.penndata import din, dinV2


@app.route('/dining/v2/venues', methods=['GET'])
def retrieve_venues_v2():
    def get_data():
        return dinV2.venues()['result_data']

    # Cache the result for 24 hours
    td = datetime.timedelta(days=1)
    return cached_route('dining:v2:venues', td, get_data)


@app.route('/dining/v2/menu/<venue_id>/<date>', methods=['GET'])
def retrieve_menu_v2(venue_id, date):
    def get_data():
        return dinV2.menu(venue_id, date)['result_data']

    # Cache the result for 24 hours
    td = datetime.timedelta(days=1)
    return cached_route('dining:v2:menu:%s:%s' % (venue_id, date), td,
                        get_data)


@app.route('/dining/v2/item/<item_id>', methods=['GET'])
def retrieve_item_v2(item_id):
    def get_data():
        return dinV2.item(item_id)['result_data']

    # Cache the result for 24 hours
    td = datetime.timedelta(days=1)
    return cached_route('dining:v2:item:%s' % item_id, td, get_data)


@app.route('/dining/venues', methods=['GET'])
def retrieve_venues():
    def get_data():
        def sortByStart(elem):
            return elem['open']

        json = din.venues()['result_data']
        venues = json['document']['venue']
        for venue in venues:
            days = venue.get('dateHours')
            if days:
                for day in days:
                    meals = day['meal']
                    new_meals = []
                    for meal in meals:
                        if venue['name'] == 'English House' and day['date'] <= '2020-03-13' and meal['type'] == 'Lunch':
                            # Hack to fix English House hours during Spring Break 2020 because Bon Appetit won't do it
                            # THIS SHOULD BE REMOVED AFTER SPRING BREAK
                            continue
                        new_meals.append(meal)
                    new_meals.sort(key=sortByStart)
                    day['meal'] = new_meals

            imageUrlJSON = db.get('venue:%s' % (str(venue['id'])))
            if imageUrlJSON:
                venue['imageURL'] = imageUrlJSON.decode('utf8').replace('\"', '')
            else:
                venue['imageURL'] = None
        return json

    # Cache the result for 24 hours
    # TEMPORARILY CHANGED CACHE TO 15 MINUTES WHILE BON APPETIT WORKS TO FIX API
    td = datetime.timedelta(minutes=15)
    return cached_route('dining:venues', td, get_data)


@app.route('/dining/hours/<venue_id>', methods=['GET'])
def retrieve_hours(venue_id):
    def get_data():
        return dinV2.hours(venue_id)['result_data']

    # Cache the result for 24 hours
    td = datetime.timedelta(days=1)
    return cached_route('dining:v2:hours:%s' % venue_id, td, get_data)


@app.route('/dining/weekly_menu/<venue_id>', methods=['GET'])
def retrieve_weekly_menu(venue_id):
    # Cache the result for 24 hours
    td = datetime.timedelta(days=1)

    def get_data():
        menu = din.menu_weekly(venue_id)
        return menu['result_data']

    return cached_route('dining:venues:weekly:%s' % venue_id, td, get_data)


@app.route('/dining/daily_menu/<venue_id>', methods=['GET'])
def retrieve_daily_menu(venue_id):
    now = datetime.datetime.today()
    end_time = datetime.datetime(now.year, now.month,
                                 now.day) + datetime.timedelta(hours=4)

    def get_data():
        return din.menu_daily(venue_id)['result_data']

    return cached_route('dining:venues:daily:%s' % venue_id, end_time - now,
                        get_data)
