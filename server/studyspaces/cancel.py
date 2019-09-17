import datetime
import os

import requests
from dateutil.parser import parse
from flask import jsonify, request
from penn.base import APIError

from server import app, db, sqldb

from ..base import cached_route
from ..models import StudySpacesBooking, User
from ..penndata import studyspaces, wharton
from .book import get_wharton_sessionid, save_booking, save_wharton_sessionid


@app.route('/studyspaces/cancel', methods=['POST'])
def cancel_room():
    """
    Cancels a booked room.
    """
    try:
        user = User.get_user()
    except ValueError as err:
        return jsonify({'error': str(err)})

    booking_id = request.form.get('booking_id')
    if not booking_id:
        return jsonify({'error': 'No booking id sent to server!'})
    if ',' in booking_id:
        return jsonify({'error': 'Only one booking may be cancelled at a time.'})

    booking = StudySpacesBooking.query.filter_by(booking_id=booking_id).first()
    if booking:
        if (booking.user is not None) and (booking.user != user.id):
            return jsonify({'error': 'Unauthorized: This reservation was booked by someone else.'}), 400
        if booking.is_cancelled:
            return jsonify({'error': 'This reservation has already been cancelled.'}), 400

    if booking_id.isdigit():
        sessionid = request.form.get('sessionid')
        if not sessionid:
            return jsonify({'error': 'No session id sent to server.'}), 400
        try:
            wharton.delete_booking(sessionid, booking_id)
            save_wharton_sessionid()
            if booking:
                booking.is_cancelled = True
                sqldb.session.commit()
            else:
                save_booking(
                    lid=1,
                    email=user.email,
                    booking_id=booking_id,
                    is_cancelled=True,
                    user=user.id
                )
            return jsonify({'result': [{'booking_id': booking_id, 'cancelled': True}]})
        except APIError as e:
            return jsonify({'error': str(e)}), 400
    else:
        resp = studyspaces.cancel_room(booking_id)
        if 'error' not in resp:
            if booking:
                booking.is_cancelled = True
                sqldb.session.commit()
            else:
                save_booking(
                    email=user.email,
                    booking_id=booking_id,
                    is_cancelled=True,
                    user=user.id
                )
        return jsonify({'result': resp})
