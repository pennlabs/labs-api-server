from server import app, sqldb
import datetime
import csv
import re
from flask import jsonify, request
from ..models import User, DiningPreference
from sqlalchemy import func


@app.route('/dining/preferences', methods=['POST'])
def save_dining_preferences():
    try:
        user = User.get_or_create()
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)})

    venues = request.form.get('venues')

    # delete old preferences for user
    DiningPreference.query.filter_by(user_id=user.id).delete()

    if venues:
        venue_ids = [int(x) for x in venues.split(",")]

        for venue_id in venue_ids:
            dining_preference = DiningPreference(user_id=user.id, venue_id=venue_id)
            sqldb.session.add(dining_preference)
    sqldb.session.commit()

    return jsonify({'success': True, 'error': None})


@app.route('/dining/preferences', methods=['GET'])
def get_dining_preferences():
    try:
        user = User.get_or_create()
    except ValueError:
        return jsonify({'preferences': []})

    preferences = sqldb.session.query(DiningPreference.venue_id, func.count(DiningPreference.venue_id)) \
                               .filter_by(user_id=user.id).group_by(DiningPreference.venue_id).all()
    preference_arr = [{'venue_id': x[0], 'count': x[1]} for x in preferences]
    return jsonify({'preferences': preference_arr})
