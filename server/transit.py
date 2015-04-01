from flask import request, jsonify
from server import app
import datetime
from base import *
from penndata import *
from utils import *

@app.route('/transit/stops', methods=['GET'])
def transit_stops():
  now = datetime.datetime.today()
  endDay = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1)
  def get_data():
    return transit.stopinventory()

  return cached_route('transit:stops', endDay - now, get_data)

@app.route('/transit/routing', methods=['GET'])
def fastest_route():
  now = datetime.datetime.today()
  endDay = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1)
  def get_data():
    return transit.stopinventory()
  stops = cache_get('transit:stops', endDay - now, get_data)

  stop_data = populate_stop_info(stops)

  latFrom, lonFrom = float(request.args['latFrom']), float(request.args['lonFrom'])
  latTo, lonTo = float(request.args['latTo']), float(request.args['lonTo'])
  bird_dist = haversine(lonFrom, latFrom, lonTo, latTo)
  route_dict = dict()

  for stop in stop_data:
    if 'routes' in stop:
      distFrom = haversine(lonFrom, latFrom, float(stop["Longitude"]), float(stop["Latitude"]))
      distTo = haversine(lonTo, latTo, float(stop["Longitude"]), float(stop["Latitude"]))

      # Update the corresponding closest from and to stops for each route
      for route_tup in stop['routes']:
        route = route_tup[0]
        order = route_tup[1]

        if route not in route_dict:
          route_dict[route] = {
            'walkingDistanceBefore': distFrom,
            'fromStop': stop,
            'fromOrder': order,
            'walkingDistanceAfter': distTo,
            'toStop': stop,
            'toOrder': order
          }
        else:
          if distFrom < route_dict[route]['walkingDistanceBefore']:
            route_dict[route]['walkingDistanceBefore'] = distFrom
            route_dict[route]['fromStop'] = stop
            route_dict[route]['fromOrder'] = order
          elif distTo < route_dict[route]['walkingDistanceAfter']:
            route_dict[route]['walkingDistanceAfter'] = distTo
            route_dict[route]['toStop'] = stop
            route_dict[route]['toOrder'] = order

  # Filter out route suggestions going the wrong way
  good_routes = filter(lambda x: route_dict[x]['fromOrder'] < route_dict[x]['toOrder'], route_dict.keys())

  if len(good_routes) == 0:
    return jsonify({"Error": "We couldn't find a helpful Penn Transit route for those locations."})
  # Choose the route with the minimum total walking distance
  final_route = min(good_routes, key=lambda x: route_dict[x]['walkingDistanceBefore']+route_dict[x]['walkingDistanceAfter'])

  info = route_dict[final_route]
  if info['walkingDistanceBefore'] + info['walkingDistanceAfter'] > bird_dist:
    return jsonify({"Error": "We couldn't find a helpful Penn Transit route for those locations."})
  info['route'] = final_route
  if 'routes' in info['toStop']:
    del info['toStop']['routes']
  if 'routes' in info['fromStop']:
    del info['fromStop']['routes']
  del info['fromOrder']
  del info['toOrder']
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
