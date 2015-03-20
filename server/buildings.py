from flask import request, json, jsonify
from server import app, db
import datetime
from base import *
from penndata import *
from utils import *

@app.route('/buildings/<building_code>', methods=['GET'])
def building(building_code):
  if db.exists("buildings:%s" % (building_code)):
    building_info = db.get("buildings:%s" % (building_code))
    return jsonify(json.loads(building_info))
  else:
    return None

@app.route('/buildings/search', methods=['GET'])
def building_search():
  search_query = request.args['q']
  td = datetime.timedelta(days=30)
  def get_data():
    data = map_search.search(search_query)
    if data is None:
      return {"Error": "The search query could not be processed"}
    else:
      return data

  return cached_route('building_search:%s' % search_query, td, get_data)

