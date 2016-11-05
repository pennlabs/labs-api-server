from flask import jsonify
from server import app
import requests
import datetime
import ast


@app.route('/weather/', methods=['GET'])
def retrieve_weather_data():
    '''Retrieves the current weather from the Open Weather Map API.
    Stores data in a cache whenever data is retrieved; cache is updated
    if it has not been updated within 10 minutes.
    '''
    f = open('.cache', 'r')
    APPID = read_api_key()

    url = 'http://api.openweathermap.org/data/2.5/weather?q=Philadelphia&units=imperial&APPID=%s' % APPID

    contents = f.read()
    f.close()

    d = datetime.datetime.now()
    if contents != '':
        cache = contents.split("\n")
        time_stamp = cache[0]
        cached_date = datetime.datetime.strptime(time_stamp, "%m %d %Y %H %M %S")
        delta = abs(cached_date - d)
        if delta.seconds >= 600:
            g = open('.cache', 'w')
            json = update_file(g, d, url)
            g.close()
            return jsonify({'weather_data': json})
        else:
            return jsonify({'weather_data': ast.literal_eval(cache[1])})
    else:
        g = open('.cache', 'w')
        update_file(g, d, url)
        g.close()
        return jsonify({'weather_data': json})


def update_file(weather_file, date, url):
    '''Used to update the cache.

    :param weather_file: the open cache file object
    :param date: current date in datetime object
    :param url: URL of Open Weather Map API for Philly
    '''
    json = requests.get(url).json()
    time = date.strftime('%m %d %Y %H %M %S')
    weather_file.write(time + '\n' + str(json))
    return json


def read_api_key():
    '''Reads the API key in from separate file.
    '''
    g = open('.app.id', 'r')
    APPID = g.read()
    g.close()
    return APPID
