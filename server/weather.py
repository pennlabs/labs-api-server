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
    OWM_API_KEY = os.getenv('OWM_API_KEY')

    def get_data():
        url = 'http://api.openweathermap.org/data/2.5/weather?q=Philadelphia&units=imperial&APPID=%s' % OWM_API_KEY
        json = requests.get(url).json()
        return {'weather_data': json}

    td = datetime.timedelta(seconds=600)

    return cached_route('weather', td, get_data)
