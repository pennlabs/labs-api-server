from flask import request, jsonify
from .base import *
from server import app
from bs4 import BeautifulSoup
import urllib2


@app.route('/studyspaces', methods=['GET'])
def parseTimes():
	url = "http://libcal.library.upenn.edu/rooms_acc.php?gid=1799&d=2016-10-22&cap=0"
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
			dictItem['time_range'] = time
			roomTimes.append(dictItem)
	return jsonify({'studyspaces' : roomTimes})





