from flask import request, jsonify
from .base import *
from server import app
from bs4 import BeautifulSoup
from datetime import time
import urllib2

groupStudyCodes = {
	505 : "Biomedical Library - Group Study Rooms",
	13107 : "Dental Library - Group Study Rooms",
	13532 : "Dental Library - Seminar Room",
	848 : "Education Commons",
	1819 : "Glossberg Record Room",
	13489 : "Levin Building Group Study Rooms",
	1768 : "Lippincott Library",
	2587 : "Lippincott Library Seminar Rooms",
	3621 : "Noldus Observer",
	1799 : "Van Pelt-Dietrich Library Center Group Study Rooms",
	4409 : "Van Pelt-Dietrich Library Center Seminar Rooms",
	1722 : "Weigle Information Commons"
} # this should be moved somewhere else

@app.route('/studyspaces/<date>', methods=['GET']) # id is given by dictionary above
def parseTimes(date): # Returns JSON with available rooms
	if 'id' in request.args:
		id = request.args['id']
		return jsonify({'studyspaces' : extractTimes(id,date)})
	else:
		l = []
		for id in groupStudyCodes:
			l += extractTimes(id,date)
		return jsonify({'studyspaces' : l})


def extractTimes(id,date):
	url = "http://libcal.library.upenn.edu/rooms_acc.php?gid=%s&d=%s&cap=0" % (int(id),date)
	soup = BeautifulSoup(urllib2.urlopen(url).read(), 'lxml')

	timeSlots = soup.find_all('form')
	unparsedRooms = timeSlots[1].contents[2:-2]

	roomTimes = []
	
	for i in unparsedRooms:
		room = BeautifulSoup(str(i),'lxml')
		try:
			roomName = room.fieldset.legend.h2.contents[0] # extract the room names
		except AttributeError:
			continue
		newRoom = str(roomName)[:-1]
		times = []

		filt = room.fieldset.find_all('label')

		for t in filt: # getting the individual times for each room 
			dictItem = {}
			dictItem['room_name'] = newRoom
			time = str(t).split("\t\t\t\t\t")[1][1:-1]
			times.append(time)
			startAndEnd = time.split(" - ")
			dictItem['start_time'] = startAndEnd[0].upper()
			dictItem['end_time'] = startAndEnd[1].upper()
			roomTimes.append(dictItem)
			dictItem['date'] = dateParse(date)
			dictItem['building'] = groupStudyCodes[int(id)]
	return roomTimes

def dateParse(d): # parses the date into a better format
	l = d.split("-")
	final = [l[1],l[2],l[0]]
	return '-'.join(final)