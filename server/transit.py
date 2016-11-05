from flask import request, jsonify
from server import app
import datetime
import copy
from functools import reduce
from time import sleep
from .base import *
from .penndata import *
from .utils import *
import requests


def get_stop_info():
    return {'result_data': populate_stop_info(transit.stopinventory())}


@app.route('/transit/stops', methods=['GET'])
def transit_stops():
    now = datetime.datetime.today()
    endDay = datetime.datetime(now.year, now.month,
                               now.day) + datetime.timedelta(days=1)

    return cached_route('transit:stops', endDay - now, get_stop_info)


@app.route('/transit/routes', methods=['GET'])
def transit_routes():
    """ Returns routes in the format:
    {
      result_data: [
        {
          route_name: "Route 1"
          stops: []
        }
      ]
    }
  """

    def get_data():
        return {'result_data': routes_with_directions(populate_route_info())}

    # cache lasts a month, since directions data is time intensive, and routes don't really change.
    data = cached_route(
        'transit:routes', datetime.timedelta(days=30), get_data)
    return data


@app.route('/transit/routing', methods=['GET'])
def fastest_route():
    """ Returns the path which routes the user to their destination with the
      shortest total walking distance.
  """
    now = datetime.datetime.today()
    endDay = datetime.datetime(now.year, now.month,
                               now.day) + datetime.timedelta(days=1)

    def get_data():
        return {'result_data': routes_with_directions(populate_route_info())}

    # Retrieve routes, generating using get_data if necessary
    route_data = cache_get('transit:routes', endDay - now,
                           get_data)['result_data']

    latFrom, lonFrom = float(request.args['latFrom']), float(request.args[
        'lonFrom'])
    latTo, lonTo = float(request.args['latTo']), float(request.args['lonTo'])

    # Total walking distance
    bird_dist = haversine(lonFrom, latFrom, lonTo, latTo)
    possible_routes = []
    for route in route_data:
        route_name = route['route_name']
        stops = route['stops']
        minFrom = -1
        minTo = -1
        fromStop = None
        toStop = None
        # Calculate the closest stops to the start and destination
        for stop in stops:
            distFrom = haversine(lonFrom, latFrom,
                                 float(stop["Longitude"]),
                                 float(stop["Latitude"]))
            distTo = haversine(lonTo, latTo,
                               float(stop["Longitude"]),
                               float(stop["Latitude"]))
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

        # If the stops found are not in the right order, this isn't a route we want
        if fromStop and toStop and fromStop['order'] < toStop['order']:

            def add_path_points(l, stop):
                if stop['order'] == fromStop['order']:
                    return l + [stop]
                else:
                    path_to = stop['path_to']
                    del stop['path_to']
                    return l + path_to + [stop]

            # Reduce the path_to field of each stop into a single path array for
            # map drawing
            path = reduce(add_path_points,
                          stops[fromStop['order']:toStop['order'] + 1], [])
            possible_routes.append({
                'route_name': route_name,
                'walkingDistanceBefore': minFrom,
                'path': path,
                'walkingDistanceAfter': minTo
            })

    if len(possible_routes) == 0:
        return jsonify({
            "Error":
            "We couldn't find a helpful Penn Transit route for those locations."
        })
    # Choose the route with the minimum total walking distance
    final_route = min(
        possible_routes,
        key=lambda x: x['walkingDistanceBefore'] + x['walkingDistanceAfter'])

    if final_route['walkingDistanceBefore'] + final_route[
            'walkingDistanceAfter'] > bird_dist:
        return jsonify({
            "Error":
            "We couldn't find a helpful Penn Transit route for those locations."
        })

    return jsonify({'result_data': final_route})


pennride_id = {"Campus Loop": 291, "PennBUS East": 229, "PennBUS West": 230}


def routes_with_directions(route_data):
    """Takes route data in the format
    [
      {
        route_name: "Route 1"
        stops: []
      },
      {
        route_name: "PennBUS West"
        stops: [
          {
            BusStopName: "The Quad, 3700 Spruce St.",
            Latitude: 39.9,
            Longitude: -75.2,
            BusStopId: 29207,
            order: 0,
            path_to: [
              {
                Latitude: 39.95,
                Longitude: -75.19
              }
            ]
          }
        ]
      }
    ]
    and populates each stop['path_to'] with map waypoints between it and the previous
    stop. These are used to give full, correct paths when routing.
  """

    def is_stop(waypoint, stop, epsilon=0.0002):
        """Return whether waypoint is actually a stop based on a margin of error"""
        diff_latitude = abs(waypoint["Latitude"] - stop["Latitude"])
        diff_longitude = abs(waypoint["Longitude"] - stop["Longitude"])
        return diff_latitude + diff_longitude > epsilon

    for route in route_data:
        url = 'http://www.pennrides.com/Route/%d/Waypoints/' % pennride_id[
            route['route_name']]
        r = requests.get(url)
        all_waypoints = r.json()[0]
        i = 0
        for stop in route['stops']:
            stop['path_to'] = []

            while is_stop(all_waypoints[i], stop):
                stop['path_to'].append(all_waypoints[i])
                i += 1
                if i >= len(all_waypoints):
                    raise ValueError('pennrides and ISC Data do not match')
            i += 1
    return route_data


def populate_stop_info(stops):
    """
    Uses transit configuration data to populate route information for each stop.
  """
    try:
        stop_dict = {
            stop['BusStopName']: stop
            for stop in stops['result_data'] if 'BusStopName' in stop
        }
        config = transit.configuration()
        for route in config['result_data']['ConfigurationData']['Route']:
            for d in route['Direction']:
                for stop in d['Stop']:
                    if stop['title'] in stop_dict:
                        if 'routes' not in stop_dict[stop['title']]:
                            stop_dict[stop['title']]['routes'] = dict()
                        stop_dict[stop['title']]['routes'][route['key']] = int(
                            stop['stopOrder'])
        return list(stop_dict.values())
    except:
        return {"error": "JSON error in building stops"}


def populate_route_info():
    """
    This function retrieves the list of stops an return a map from route names
    to corresponding arrays of stops. It also filters out all routes
    other than Campus Loop, PennBUS East, and PennBUS West. Finally, it also
    removes the last stop on the Campus Loop, which appears to be incorrect.
  """
    # retrieve from cache, or generate and store in cache
    stop_info = cache_get(
        'transit:stops', datetime.timedelta(days=1), get_stop_info)

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
        routes[route] = sorted(routes[route], key=lambda stop: stop["order"])

    # Filter out bad routes
    good_routes = ['PennBUS East', 'PennBUS West', 'Campus Loop']

    routes = [{
        'route_name': key,
        'stops': routes[key]
    } for key in routes if key in good_routes]

    return routes
