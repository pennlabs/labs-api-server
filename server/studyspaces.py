from flask import request, jsonify
from .base import *
from server import app
from bs4 import BeautifulSoup
import urllib2

@app.route('/studyspaces/<date>', methods=['GET']) # id is given by dictionary above
def parseTimes(date): # Returns JSON with available rooms
	groupStudyCodes = getIDs()
	if 'id' in request.args:
		id = request.args['id']
		return jsonify({'studyspaces' : extractTimes(id,date,groupStudyCodes)})
	else:
		l = []
		for id in groupStudyCodes:
			l += extractTimes(id,date,groupStudyCodes)
		return jsonify({'studyspaces' : l})


def extractTimes(id,date,groupStudyCodes): 
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

def getIDs(): # extracts the ID's of the room into groupStudyCodes
	groupStudyCodes = {}
	url = "http://libcal.library.upenn.edu/booking/vpdlc"
	soup = BeautifulSoup(urllib2.urlopen(url).read(), 'lxml')
	l = soup.find_all('option')
	for element in l:
		if element['value'] != '0':
			url2 = "http://libcal.library.upenn.edu" + str(element['value'])
			soup2 = BeautifulSoup(urllib2.urlopen(url2).read(), 'lxml')
			id = soup2.find('input', attrs={"id" : "gid"})['value']
			groupStudyCodes[int(id)] = element.contents[0]
	return groupStudyCodes