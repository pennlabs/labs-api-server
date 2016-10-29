from flask import request, jsonify
from .base import *
from server import app
import urllib2
import datetime

@app.route('/weather', methods=['GET'])
def retrieve():
	try:
		f = open('.cache','r+w')
	except IOError:
		f = open('.cache','w')
		f.close()
		f = open('.cache','r+w')
	g = open('.app.id','r')
	APPID = g.read()
	g.close()
	d = datetime.datetime.now()
	url = 'http://api.openweathermap.org/data/2.5/weather?q=Philadelphia&units=imperial&APPID=%s' % APPID
	json = urllib2.urlopen(url).read()
	time = d.strftime('%m %d %Y %H %M %S')
	f.write(time + "\n\n" + json)
	f.close()
	return json