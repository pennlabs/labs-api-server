from flask import request, jsonify
from server import app
from bs4 import BeautifulSoup
import requests


def get_id_json():
    """
    Extracts the ID's of the room to a JSON.
    """
    groupStudyCodes = []
    url = "http://libcal.library.upenn.edu/booking/vpdlc"
    soup = BeautifulSoup(requests.get(url).text, 'lxml')
    l = soup.find_all('option')
    for element in l:
        if element['value'] != '0':
            url2 = "http://libcal.library.upenn.edu" + str(element['value'])
            soup2 = BeautifulSoup(requests.get(url2), 'lxml')
            id = soup2.find('input', attrs={"id": "gid"})['value']
            newDict = {}
            newDict['id'] = int(id)
            newDict['name'] = element.contents[0]
            groupStudyCodes.append(newDict)
    return groupStudyCodes


def get_id_dict():
    """
    Extracts the ID's of the room into a dictionary.
    """
    groupStudyCodes = {}
    url = "http://libcal.library.upenn.edu/booking/vpdlc"
    soup = BeautifulSoup(requests.get(url).text, 'lxml')
    l = soup.find_all('option')
    for element in l:
        if element['value'] != '0':
            url2 = "http://libcal.library.upenn.edu" + str(element['value'])
            soup2 = BeautifulSoup(requests.get(url2).text, 'lxml')
            id = soup2.find('input', attrs={"id": "gid"})['value']
            groupStudyCodes[int(id)] = element.contents[0]
    return groupStudyCodes


@app.route('/studyspaces/<date>', methods=['GET'])
def parse_times(date):
    """
    Returns JSON with available rooms.
    """
    d = get_id_dict()
    if 'id' in request.args:
        id = request.args['id']
        return jsonify({'studyspaces': extract_times(id, date, d[int(id)])})
    else:
        m = []
        for element in d:
            m += extract_times(element, date, d[element])
        return jsonify({'studyspaces': m})


def extract_times(id, date, name):
    """
    Scrapes the avaiable rooms with the given ID and date.
    """
    url = "http://libcal.library.upenn.edu/rooms_acc.php?gid=%s&d=%s&cap=0" % (int(id), date)
    soup = BeautifulSoup(requests.get(url).text, 'lxml')

    timeSlots = soup.find_all('form')
    unparsedRooms = timeSlots[1].contents[2:-2]

    roomTimes = []

    for i in unparsedRooms:
        room = BeautifulSoup(str(i), 'lxml')
        try:
            # extract room names
            roomName = room.fieldset.legend.h2.contents[0]
        except AttributeError:
            # in case the contents aren't a list
            continue
        newRoom = str(roomName)[:-1]
        times = []

        filt = room.fieldset.find_all('label')

        for t in filt:
            # getting the individual times for each room
            dictItem = {}
            dictItem['room_name'] = newRoom
            time = str(t).split("\t\t\t\t\t")[1][1:-1]
            times.append(time)
            startAndEnd = time.split(" - ")
            dictItem['start_time'] = startAndEnd[0].upper()
            dictItem['end_time'] = startAndEnd[1].upper()
            roomTimes.append(dictItem)
            dictItem['date'] = date_parse(date)
            dictItem['building'] = name
    return roomTimes


def date_parse(d):  
    """
    Parses the date to dashed format.
    """
    l = d.split("-")
    final = [l[1], l[2], l[0]]
    return '-'.join(final)


@app.route('/studyspaceid', methods=['GET'])
def display():
    """
    Returns JSON containing which ID corresponds to what room.
    """
    return jsonify({'studyspaceid': get_id_json()})
