from flask import Flask, g, session, jsonify, Response, request, json, render_template, redirect, current_app, jsonify
from server import app, db
from werkzeug.security import generate_password_hash, check_password_hash
import json
import string
import datetime
from bson.objectid import ObjectId
import re
import requests
from penndata import *
from utils import *

# Dining API
@app.route('/dining/venues', methods=['GET'])
def retrieve_venues():
  now = datetime.datetime.today()
  daysTillWeek = 6 - now.weekday()
  td = datetime.timedelta(days = daysTillWeek)
  month = now + td
  month.replace(hour=23, minute=59, second=59)
  if (db.exists('dining:venues')):
    return jsonify(json.loads(db.get('dining:venues')))
  else:
    venues = din.venues()
    db.set('dining:venues', json.dumps(venues["result_data"]))
    db.pexpireat('dining:venues', month)
    return jsonify(venues["result_data"])


@app.route('/dining/weekly_menu/<venue_id>', methods=['GET'])
def retrieve_weekly_menu(venue_id):
  now = datetime.datetime.today()
  daysTillWeek = 6 - now.weekday()
  endWeek = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=daysTillWeek);
  venue_id = venue_id
  if (db.exists("dining:venues:weekly:%s" % (venue_id))):
    return jsonify(json.loads(db.get("dining:venues:weekly:%s" % (venue_id))))
  else:
    menu = din.menu_weekly(venue_id)
    if venue_id == "638":
      menu["result_data"]["Document"]["location"] = "University of Pennsylvania Kosher Dining at Falk"
    db.set('dining:venues:weekly:%s' % (venue_id), json.dumps(menu["result_data"]))
    db.pexpireat('dining:venues:weekly:%s' % (venue_id), endWeek)
    return jsonify(menu["result_data"])


@app.route('/dining/daily_menu/<venue_id>', methods=['GET'])
def retrieve_daily_menu(venue_id):
  now = datetime.datetime.today()
  endDay = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1)
  venue_id = venue_id
  if (db.exists("dining:venues:daily:%s" % (venue_id))):
    return jsonify(json.loads(db.get("dining:venues:daily:%s" % (venue_id))))
  else:
    menu = din.menu_daily(venue_id)
    db.set('dining:venues:daily:%s' % (venue_id), json.dumps(menu["result_data"]))
    db.pexpireat('dining:venues:daily:%s' % (venue_id), endDay)
    return jsonify(menu["result_data"])


# Directory API
@app.route('/directory/search', methods=['GET'])
def detail_search():

  if not request.args.has_key('name'):
    return jsonify({"error": "Please specify search parameters in the query string"})

  name = request.args['name']
  arr = name.split()
  params = []

  if (db.exists("directory:search:%s" % (name))):
    return jsonify(json.loads(db.get("directory:search:%s" % (name))))

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

  now = datetime.datetime.today()
  td = datetime.timedelta(days = 30)
  month = now + td

  final = {'result_data':final}

  db.set('directory:search:%s' % (name), json.dumps(final))
  db.pexpireat('directory:search:%s' % (name), month)
  return jsonify(final)


@app.route('/directory/person/<person_id>', methods=['GET'])
def person_details(person_id):
  now = datetime.datetime.today()
  td = datetime.timedelta(days = 30)
  month = now + td
  if (db.exists("directory:person:%s" % (person_id))):
    return jsonify(json.loads(db.get("directory:person:%s" % (person_id))))
  else:
    data = penn_dir.person_details(person_id)
    db.set('directory:person:%s' % (person_id), json.dumps(data["result_data"][0]))
    db.pexpireat('directory:person:%s' % (person_id), month)
    return jsonify(data["result_data"][0])

def is_dept(keyword):
  return keyword.upper() in depts.keys()


def get_serializable_course(course):
  return {
    '_id': str(course.get('_id', '')),
    'dept': course.get('dept', ''),
    'title': course.get('title', ''),
    'courseNumber': course.get('courseNumber', ''),
    'credits': course.get('credits'),
    'sectionNumber': course.get('sectionNumber', ''),
    'type': course.get('type', ''),
    'times': course.get('times', ''),
    'days': course.get('days', ''),
    'hours': course.get('hours', ''),
    'building': course.get('building'),
    'roomNumber': course.get('roomNumber'),
    'prof': course.get('prof')
  }

def search_course(course):
  params = dict()
  if len(course.get('dept', '')) > 0:
    id_param = ""
    id_param += course.get('dept').lower()
    if len(course.get('courseNumber', '')) > 0:
      id_param += "-" + course.get('courseNumber').lower()
      if len(course.get('sectionNumber', '')) > 0:
        id_param += course.get('sectionNumber').lower()
    params['course_id'] = id_param

  if len(course['desc_search']) > 0:
    params['description'] = course['desc_search']

  if len(params) == 0:
    return None
  final_courses = reg.search(params)
  return {"courses" : list(final_courses)}

def get_type_search(search_query):
  course = {'courseNumber': '',
        'sectionNumber': '',
        'dept': '',
        'desc_search': ''}
  search_punc = re.sub('[%s]' % re.escape(string.punctuation), ' ', search_query)
  def repl(matchobj):
    return matchobj.group(0)[0] + " " + matchobj.group(0)[1]
  search_presplit = re.sub('(\d[a-zA-z]|[a-zA-z]\d)', repl, search_punc)
  split = search_presplit.split()
  found_desc = False
  in_desc = False
  for s in split:
    s = s.strip()
    if s.isalpha() and is_dept(s.upper()):
      in_desc = False
      course['dept'] = s.upper()
    elif s.isdigit():
      in_desc = False
      if (len(s) == 3):
        course['courseNumber'] = s
      if (len(s) == 6):
        course['courseNumber'] = s[:3]
        course['sectionNumber'] = s[-3:]
    else:
      if not found_desc or in_desc:
        found_desc = True
        in_desc = True
        if len(course['desc_search']) == 0:
          course['desc_search'] = s
        else:
          course['desc_search'] += " " + s
  return course


@app.route('/registrar/search', methods=['GET'])
def search():
  search_query = request.args['q']
  now = datetime.datetime.today()
  endDay = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1)
  if (db.exists('registrar_query:%s' % search_query)):
    return jsonify(json.loads(db.get('registrar_query:%s' % search_query)))
  else:
    query_results = search_course(get_type_search(search_query))
  if query_results is None:
    return jsonify({"Error": "The search query could not be processed"})
  db.set('registrar_query:%s' % search_query,  json.dumps(query_results))
  db.pexpireat('registrar_query:%s' % search_query, endDay)
  return jsonify(query_results)

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
  now = datetime.datetime.today()
  endMonth = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=30)
  if (db.exists('building_search:%s' % search_query)):
    return jsonify(json.loads(db.get('building_search:%s' % search_query)))
  else:
    query_results = map_search.search(search_query)
  if query_results is None:
    return jsonify({"Error": "The search query could not be processed"})
  db.set('building_search:%s' % search_query,  json.dumps(query_results))
  db.pexpireat('building_search:%s' % search_query, endMonth)
  return jsonify(query_results)

@app.route('/transit/stops', methods=['GET'])
def transit_stops():
  return jsonify(get_stops())

def get_stops():
  now = datetime.datetime.today()
  endDay = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1)

  if (db.exists('transit:stops')):
    stops = db.get('transit:stops')
    return json.loads(stops)
  else:
    stops = transit.stopinventory()

    db.set('transit:stops', json.dumps(stops))
    db.pexpireat('transit:stops', endDay)
    return stops

@app.route('/transit/routing', methods=['GET'])
def fastest_route():
  stops = get_stops()
  stop_data = populate_stop_info(stops)

  latFrom, lonFrom = float(request.args['latFrom']), float(request.args['lonFrom'])
  latTo, lonTo = float(request.args['latTo']), float(request.args['lonTo'])
  bird_dist = haversine(lonFrom, latFrom, lonTo, latTo)
  route_dict = dict()

  for stop in stop_data:
    if 'routes' in stop:
      distFrom = haversine(lonFrom, latFrom, float(stop["Longitude"]), float(stop["Latitude"]))
      distTo = haversine(lonTo, latTo, float(stop["Longitude"]), float(stop["Latitude"]))

      # Update the corresponding closes from and to stops for each route
      for route_tup in stop['routes']:
        route = route_tup[0]
        order = route_tup[1]

        if route not in route_dict:
          route_dict[route] = {
            'minFrom': distFrom,
            'fromStop': stop['BusStopName'],
            'fromOrder': order,
            'minTo': distTo,
            'toStop': stop['BusStopName'],
            'toOrder': order
          }
        else:
          if distFrom < route_dict[route]['minFrom']:
            route_dict[route]['minFrom'] = distFrom
            route_dict[route]['fromStop'] = stop['BusStopName']
            route_dict[route]['fromOrder'] = order
          elif distTo < route_dict[route]['minTo']:
            route_dict[route]['minTo'] = distTo
            route_dict[route]['toStop'] = stop['BusStopName']
            route_dict[route]['toOrder'] = order

  # Filter out route suggestions going the wrong way
  good_routes = filter(lambda x: route_dict[x]['fromOrder'] < route_dict[x]['toOrder'], route_dict.keys())

  if len(good_routes) == 0:
    return jsonify({"Error": "We couldn't find a helpful Penn Transit route for those locations."})
  # Choose the route with the minimum total walking distance
  final_route = min(good_routes, key=lambda x: route_dict[x]['minTo']+route_dict[x]['minFrom'])

  info = route_dict[final_route]
  if info['minTo'] + info['minFrom'] > bird_dist:
    return jsonify({"Error": "We couldn't find a helpful Penn Transit route for those locations."})
  info['route'] = final_route
  return jsonify(info)


def populate_stop_info(stops):
  try:
    stop_dict = {stop['BusStopName']: stop for stop in stops['result_data'] if 'BusStopName' in stop}
    config = transit.configuration()
    for route in config['result_data']['ConfigurationData']['Route']:
      for d in route['Direction']:
        for stop in d['Stop']:
          if stop['title'] in stop_dict:
            if 'routes' not in stop_dict[stop['title']]:
              stop_dict[stop['title']]['routes'] = set()
            stop_dict[stop['title']]['routes'].add((route['key'], int(stop['stopOrder'])))

    for key in stop_dict:
      if 'routes' in stop_dict[key]:
        stop_dict[key]['routes'] = list(stop_dict[key]['routes'])
    return stop_dict.values()
  except Exception:
    print "JSON Error in building stops"
    return {}


