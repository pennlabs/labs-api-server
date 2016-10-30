from flask import request, jsonify
from server import app
from .penndata import *


@app.route('/studyspaces/avail/<date>', methods=['GET'])
def parse_times(date):
    """
    Returns JSON with available rooms.

    Usage:
        /studyspaces/avail/<date> gives all available
        /studyspaces/avail/<date>?id=<id> gives the avaiable room with <id>
    """
    d = get_id_dict()
    if 'id' in request.args:
        try:
            id = request.args['id']
        except KeyError:
            # check for invalid ID's
            return jsonify({'studyspaces': "Invalid ID number."})
        return jsonify({'studyspaces': extract_times(id, date, d[int(id)])})
    else:
        m = []
        for element in d:
            m += extract_times(element, date, d[element])
        return jsonify({'studyspaces': m})


@app.route('/studyspaces/ids', methods=['GET'])
def display_id_pairs():
    """
    Returns JSON containing which ID corresponds to what room.
    """
    return jsonify({'studyspaceid': get_id_json()})
