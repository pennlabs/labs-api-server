from server import app
from .base import cached_route
import requests
import datetime


@app.route('/weather/', methods=['GET'])
def retrieve_weather_data():
    '''Retrieves the current weather from the Open Weather Map API.
    Stores data in a cache whenever data is retrieved; cache is updated
    if it has not been updated within 10 minutes.
    '''
    APPID = read_api_key()

    def get_data():
        url = 'http://api.openweathermap.org/data/2.5/weather?q=Philadelphia&units=imperial&APPID=%s' % APPID
        json = requests.get(url).json()
        print json
        return {'weather': json}

    td = datetime.timedelta(seconds=600)

    return cached_route('weather', td, get_data)


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
