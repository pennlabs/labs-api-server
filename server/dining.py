from server import app
import datetime
from base import *
from penndata import *
from utils import *


@app.route('/dining/venues', methods=['GET'])
def retrieve_venues():
  def get_data():
    return din.venues()['result_data']
  now = datetime.datetime.today()
  daysTillWeek = 6 - now.weekday()
  td = datetime.timedelta(days=daysTillWeek)
  return cached_route('dining:venues', td, get_data)


@app.route('/dining/weekly_menu/<venue_id>', methods=['GET'])
def retrieve_weekly_menu(venue_id):
  now = datetime.datetime.today()
  daysTillWeek = 6 - now.weekday()
  td = datetime.timedelta(days=daysTillWeek)
  def get_data():
    menu = din.menu_weekly(venue_id)
    if venue_id == "638":
      menu["result_data"]["Document"]["location"] = "University of Pennsylvania Kosher Dining at Falk"
    return menu["result_data"]
  return cached_route('dining:venues:weekly:%s' % venue_id, td, get_data)

@app.route('/dining/daily_menu/<venue_id>', methods=['GET'])
def retrieve_daily_menu(venue_id):
  now = datetime.datetime.today()
  end_time = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(hours=4)
  def get_data():
    return din.menu_daily(venue_id)["result_data"]
  return cached_route('dining:venues:daily:%s' % venue_id, end_time - now, get_data)
