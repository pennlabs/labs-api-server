from flask import request, jsonify
from .base import *
from server import app
from bs4 import BeautifulSoup
from datetime import time
import urllib2


@app.route('/studyspaces/<id>/<date>', methods=['GET'])
def parseTimes(id,date):
	url = "http://libcal.library.upenn.edu/rooms_acc.php?gid=%s&d=%s&cap=0" % (id,date)
	soup = BeautifulSoup(urllib2.urlopen(url).read(), 'lxml')

	timeSlots = soup.find_all('form')
	unparsedRooms = timeSlots[1].contents[2:-2]

	roomTimes = []
	
	for i in unparsedRooms:
		room = BeautifulSoup(str(i),'lxml')
		roomName = room.fieldset.legend.h2.contents[0] # extract the room names
		newRoom = str(roomName)[:-1]
		times = []

		for t in room.fieldset.find_all('label'):
			dictItem = {}
			dictItem['room_name'] = newRoom
			time = str(t).split("\t\t\t\t\t")[1][1:-1]
			times.append(time)
			startAndEnd = time.split(" - ")
			dictItem['start_time'] = startAndEnd[0].upper()
			dictItem['end_time'] = startAndEnd[1].upper()
			roomTimes.append(dictItem)
			dictItem['date'] = dateParse(date)
	return jsonify({'studyspaces' : roomTimes})

def dateParse(d):
	l = d.split("-")
	final = [l[1],l[2],l[0]]
	return '-'.join(final)