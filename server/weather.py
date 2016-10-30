from flask import request, jsonify
from server import app
import requests
import datetime


@app.route('/weather', methods=['GET'])
def retrieve():
    try:
        f = open('.cache', 'r+w')
    except IOError:
        # if file does not exist
        f = open('.cache', 'w')
        f.close()
        f = open('.cache', 'r+w')
    g = open('.app.id', 'r')
    APPID = g.read()
    g.close()

    contents = f.read()
    if contents != '':
        d = datetime.datetime.now()
        cache = contents.split("\n")
        time_stamp = cache[0]
        cached_date = datetime.datetime.strptime(time_stamp, "%m %d %Y %H %M %S")
        delta = abs(cached_date - d)
        if delta.seconds >= 600:
            url = 'http://api.openweathermap.org/data/2.5/weather?q=Philadelphia&units=imperial&APPID=%s' % APPID
            json = requests.get(url).json()
            time = d.strftime('%m %d %Y %H %M %S')
            f.write(time + "\n" + json)
            f.close()
            return json
        else:
            f.close()
            return cache[1]
