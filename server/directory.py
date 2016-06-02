from flask import request, jsonify
from server import app
import datetime
from .base import *
from .penndata import *
from .utils import *


@app.route('/directory/search', methods=['GET'])
def detail_search():
  if not request.args.has_key('name'):
    return jsonify({"error": "Please specify search parameters in the query string"})

  name = request.args['name']

  def get_data():

    arr = name.split()
    params = []

    if len(arr) > 1:

      if arr[0][-1] == ',':
        params = [{'last_name':arr[0][:-1], 'first_name':arr[1]}]
      else:
        params = [
          {'last_name':arr[-1], 'first_name':arr[0]},
          {'last_name':arr[0], 'first_name':arr[-1]}
        ]

    else:
      params = [{'last_name':name},{'first_name':name}]

    ids = set()
    final = []
    for param in params:
      param['affiliation'] = 'FAC'
    for param in params:
      data = penn_dir.search(param)
      for result in data['result_data']:
        person_id = result['person_id']
        if person_id not in ids:
          final.append(result)
          ids.add(person_id)

    return {'result_data':final}

  td = datetime.timedelta(days = 30)
  return cached_route('directory:search:%s' % name, td, get_data)



@app.route('/directory/person/<person_id>', methods=['GET'])
def person_details(person_id):
  td = datetime.timedelta(days = 30)
  def get_data():
    return penn_dir.person_details(person_id)['result_data'][0]

  return cached_route('directory:person:%s' % person_id, td, get_data)
