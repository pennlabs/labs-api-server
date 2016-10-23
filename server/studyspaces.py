from flask import request, jsonify
from .base import *
from server import app
from bs4 import BeautifulSoup
from datetime import time
import urllib2

groupStudyCodes = {
	"Biomedical Library - Group Study Rooms" : 505,
	"Dental Library - Group Study Rooms" : 13107,
	"Dental Library - Seminar Room" : 13532,
	"Education Commons" : 848,
	"Glossberg Record Room" : 1819,
	"Levin Building Group Study Rooms" : 13489,
	"Lippincott Library" : 1768,
	"Lippincott Library Seminar Rooms" : 2587,
	"Noldus Observer" : 3621,
	"Van Pelt-Dietrich Library Center Group Study Rooms" : 1799,
	"Van Pelt-Dietrich Library Center Seminar Rooms" : 4409,
	"Weigle Information Commons" : 1722
} # this should be moved somewhere else

@app.route('/studyspaces/<date>', methods=['GET']) # id is given by dictionary above
def parseTimes(date): # Returns JSON with available rooms
	id = request.args['id']
	print request.args
	if(id != None):
		return jsonify({'studyspaces' : extractTimes(id,date)})
	else:
		l = []
		for key in groupStudyCodes:
			l += extractTimes(groupStudyCodes[key],date)
		return jsonify({'studyspaces' : l})


def extractTimes(id,date):
	url = "http://libcal.library.upenn.edu/rooms_acc.php?gid=%s&d=%s&cap=0" % (id,date)
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

	return {'studyspaces' : roomTimes}

def dateParse(d):
	l = d.split("-")
	final = [l[1],l[2],l[0]]
	return '-'.join(final)