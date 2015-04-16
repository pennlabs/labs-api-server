from flask import request, jsonify
from server import app
import datetime
import copy
from time import sleep
from base import *
from penndata import *
from utils import *
import requests
from os import getenv


def get_stop_info():
  return {'result_data': populate_stop_info(transit.stopinventory())}

@app.route('/transit/stops', methods=['GET'])
def transit_stops():
  now = datetime.datetime.today()
  endDay = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1)

  return cached_route('transit:stops', endDay - now, get_stop_info)

@app.route('/transit/routes', methods=['GET'])
def transit_routes():
  def get_data():
    return {'result_data': routes_with_directions(populate_route_info())}

  # cache lasts a month, since directions data is time intensive, and routes don't really change.
  data = cached_route('transit:routes', datetime.timedelta(days=30), get_data)
  return data

@app.route('/transit/routing', methods=['GET'])
def fastest_route():
  now = datetime.datetime.today()
  endDay = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1)

  def get_data():
    return {'result_data': populate_route_info()}

  route_data = cache_get('transit:routes', endDay - now, get_data)['result_data']

  latFrom, lonFrom = float(request.args['latFrom']), float(request.args['lonFrom'])
  latTo, lonTo = float(request.args['latTo']), float(request.args['lonTo'])
  bird_dist = haversine(lonFrom, latFrom, lonTo, latTo)
  possible_routes = []
  for route_name, stops in route_data.items():
    minFrom = -1
    minTo = -1
    fromStop = None
    toStop = None
    for stop in stops:

      distFrom = haversine(lonFrom, latFrom, float(stop["Longitude"]), float(stop["Latitude"]))
      distTo = haversine(lonTo, latTo, float(stop["Longitude"]), float(stop["Latitude"]))
      if minFrom == -1:
        fromStop = stop
        minFrom = distFrom
      elif distFrom < minFrom:
        fromStop = stop
        minFrom = distFrom

      if minTo == -1:
        minTo = distTo
        toStop = stop
      elif distTo < minTo:
        minTo = distTo
        toStop = stop

    if fromStop and toStop and fromStop['order'] < toStop['order']:
      def add_path_points(l, stop):
        if stop['order'] == fromStop['order']:
          return l + [stop]
        else:
          path_to = stop['path_to']
          del stop['path_to']
          return l + path_to + [stop]

      path = reduce(add_path_points, stops[fromStop['order']:toStop['order']+1], [])
      possible_routes.append({
        'route_name': route_name,
        'walkingDistanceBefore': minFrom,
        'path': path,
        'walkingDistanceAfter': minTo
        })


  if len(possible_routes) == 0:
    return jsonify({"Error": "We couldn't find a helpful Penn Transit route for those locations."})
  # Choose the route with the minimum total walking distance
  final_route = min(possible_routes, key=lambda x: x['walkingDistanceBefore'] + x['walkingDistanceAfter'])

  if final_route['walkingDistanceBefore'] + final_route['walkingDistanceAfter'] > bird_dist:
    return jsonify({"Error": "We couldn't find a helpful Penn Transit route for those locations."})

  return jsonify({'result_data': final_route})

def routes_with_directions(route_data):
  for route_name, stops in route_data.items():
    for i in xrange(len(stops)-1):
      latFrom = stops[i]["Latitude"]
      lonFrom = stops[i]["Longitude"]
      latTo = stops[i+1]["Latitude"]
      lonTo = stops[i+1]["Longitude"]

      r = requests.get('https://maps.googleapis.com/maps/api/directions/json?key=%s&origin=%.8f,%.8f&destination=%.8f,%.8f' %
      (getenv('GOOGLEMAPS_API_KEY'), latFrom, lonFrom, latTo, lonTo) )
      # rate limiting
      sleep(2)
      json_data = r.json()
      if json_data['status'] != 'OK':
        raise ValueError(json_data['error_message'])
      else:
        steps = json_data['routes'][0]['legs'][0]['steps']
        stops[i+1]['path_to'] = map(lambda step: {'Latitude':  step['end_location']['lat'], 'Longitude': step['end_location']['lng']}, steps)
  return route_data



def populate_stop_info(stops):
  try:
    stop_dict = {stop['BusStopName']: stop for stop in stops['result_data'] if 'BusStopName' in stop}
    config = transit.configuration()
    for route in config['result_data']['ConfigurationData']['Route']:
      for d in route['Direction']:
        for stop in d['Stop']:
          if stop['title'] in stop_dict:
            if 'routes' not in stop_dict[stop['title']]:
              stop_dict[stop['title']]['routes'] = dict()
            stop_dict[stop['title']]['routes'][route['key']] = int(stop['stopOrder'])
    return stop_dict.values()
  except Exception:
    print "JSON Error in building stops"
    return {}

def populate_route_info():
  stop_info = cache_get('transit:stops', datetime.timedelta(days=1), get_stop_info)
  routes = dict()
  for stop in stop_info['result_data']:
    if 'routes' in stop:
      items = stop['routes'].items()
      del stop['routes']
      for route_name, val in items:
        to_insert = copy.deepcopy(stop)
        to_insert["order"] = val

        if route_name in routes:
          routes[route_name].append(to_insert)
        else:
          routes[route_name] = [to_insert]
  for route in routes:
    routes[route] = sorted(routes[route], key= lambda stop: stop["order"])
  good_routes = ['PennBUS East', 'PennBUS West', 'Campus Loop']
  routes = {key: routes[key] for key in routes if key in good_routes}

  return routes
