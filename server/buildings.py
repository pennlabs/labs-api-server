import datetime

from flask import json, jsonify, request

from server import app, db

from .base import cached_route
from .penndata import map_search


@app.route('/buildings/<building_code>', methods=['GET'])
def building(building_code):
    if db.exists('buildings:%s' % (building_code)):
        building_info = db.get('buildings:%s' % (building_code)).decode('utf8')
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
            return {'Error': 'The search query could not be processed'}
        else:
            return data

    return cached_route('building_search:%s' % search_query, td, get_data)
