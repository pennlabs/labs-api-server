from flask import request, jsonify
from server import app
import datetime
import copy
from base import *
from penndata import *
from utils import *


def get_stop_info():
  return {'result_data': populate_stop_info(transit.stopinventory())}

@app.route('/transit/stops', methods=['GET'])
def transit_stops():
  now = datetime.datetime.today()
  endDay = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1)

  return cached_route('transit:stops', endDay - now, get_stop_info)

@app.route('/transit/routes', methods=['GET'])
def transit_routes():
  now = datetime.datetime.today()
  endDay = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1)
  def get_data():
    return {'result_data': populate_route_info()}

  return cached_route('transit:routes', endDay - now, get_data)

@app.route('/transit/routing', methods=['GET'])
def fastest_route():
  now = datetime.datetime.today()
  endDay = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1)

  def get_data():
    return {'result_data': populate_route_info()}

  route_data = cache_get('transit:routes', endDay - now, get_data)['result_data']

  good_routes = ['PennBUS East', 'PennBUS West', 'Campus Loop']

  route_data = {key: route_data[key] for key in route_data if key in good_routes}

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
      possible_routes.append({
        'route_name': route_name,
        'walkingDistanceBefore': minFrom,
        'path': stops[fromStop['order']:toStop['order']+1],
        'walkingDistanceAfter': minTo
        })


  if len(possible_routes) == 0:
    return jsonify({"Error": "We couldn't find a helpful Penn Transit route for those locations."})
  # Choose the route with the minimum total walking distance
  final_route = min(possible_routes, key=lambda x: x['walkingDistanceBefore'] + x['walkingDistanceAfter'])

  if final_route['walkingDistanceBefore'] + final_route['walkingDistanceAfter'] > bird_dist:
    return jsonify({"Error": "We couldn't find a helpful Penn Transit route for those locations."})

  return jsonify({'result_data': final_route})

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
  return routes