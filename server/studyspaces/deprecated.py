from flask import jsonify, request
from penn.base import APIError

from server import app
from server.penndata import wharton
from server.studyspaces.book import get_wharton_sessionid, save_wharton_sessionid


@app.route('/studyspaces/gsr', methods=['GET'])
def get_wharton_gsrs_temp_route():
    """ Temporary endpoint to allow non-authenticated users to access the list of GSRs. """
    date = request.args.get('date')
    try:
        data = wharton.get_wharton_gsrs(get_wharton_sessionid(public=True), date)
        save_wharton_sessionid()
        return jsonify(data)
    except APIError as error:
        return jsonify({'error': str(error)}), 400


@app.route('/studyspaces/gsr/reservations', methods=['GET'])
def get_wharton_gsr_reservations():
    """
    Returns JSON containing a list of Wharton GSR reservations.
    """

    sessionid = get_wharton_sessionid()

    if not sessionid:
        return jsonify({'error': 'No Session ID provided.'})

    try:
        reservations = wharton.get_reservations(sessionid)
        save_wharton_sessionid()
        return jsonify({'reservations': reservations})
    except APIError as e:
        return jsonify({'error': str(e)}), 400


@app.route('/studyspaces/gsr/delete', methods=['POST'])
def delete_wharton_gsr_reservation():
    """
    Deletes a Wharton GSR reservation
    """
    booking = request.form.get('booking')
    sessionid = request.form.get('sessionid')
    if not booking:
        return jsonify({'error': 'No booking sent to server.'})
    if not sessionid:
        return jsonify({'error': 'No session id sent to server.'})

    try:
        result = wharton.delete_booking(sessionid, booking)
        save_wharton_sessionid()
        return jsonify({'result': result})
    except APIError as e:
        return jsonify({'error': str(e)}), 400
