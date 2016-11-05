from server import app
from .base import cached_route
import requests
import datetime
import os


@app.route('/weather/', methods=['GET'])
def retrieve_weather_data():
    '''Retrieves the current weather from the Open Weather Map API.
    Stores data in a cache whenever data is retrieved; cache is updated
    if it has not been updated within 10 minutes.
    '''
    read_api_key()

    def get_data():
        url = 'http://api.openweathermap.org/data/2.5/weather?q=Philadelphia&units=imperial&APPID=%s' % os.environ['APPID']
        json = requests.get(url).json()
        return {'weather_data': json}

    td = datetime.timedelta(seconds=50)

    return cached_route('weather', td, get_data)


def read_api_key():
    '''Reads the API key in from separate file.
    '''
    g = open('.app.id', 'r')
    APPID = g.read()
    os.environ['APPID'] = APPID
