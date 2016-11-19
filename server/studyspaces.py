from flask import request, jsonify
from server import app
from .penndata import studyspaces


@app.route('/studyspaces/<date>', methods=['GET'])
def parse_times(date):
    """
    Returns JSON with available rooms.

    Usage:
        /studyspaces/avail/<date> gives all available
        /studyspaces/avail/<date>?id=<id> gives the avaiable room with <id>
    """
    d = studyspaces.get_id_dict()
    if 'id' in request.args:
        id = request.args['id']
        try:
            name = d[int(id)]
        except KeyError:
            # check for invalid ID's
            return jsonify({'error': "Invalid ID number."})
        return jsonify({
            'studyspaces': studyspaces.extract_times(id, date, name)
        })
    else:
        m = []
        for element in d:
            m += studyspaces.extract_times(element, date, d[element])
        return jsonify({'studyspaces': m})


@app.route('/studyspaces/', methods=['GET'])
def display_id_pairs():
    """
    Returns JSON containing which ID corresponds to what room.
    """
    return jsonify({'studyspaces': studyspaces.get_id_json()})
