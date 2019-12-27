from flask import g, jsonify, request
from sqlalchemy import func

from server import app, sqldb
from server.auth import auth
from server.models import DiningPreference, User


@app.route('/dining/preferences', methods=['POST'])
@auth(nullable=True)
def save_dining_preferences():
    try:
        user = User.get_or_create()
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)})

    venues = request.form.get('venues')

    # delete old preferences for user
    DiningPreference.query.filter_by(user_id=user.id).delete()

    if venues:
        venue_ids = [int(x) for x in venues.split(',')]

        account_id = g.account.id if g.account else None
        for venue_id in venue_ids:
            dining_preference = DiningPreference(user_id=user.id, account=account_id, venue_id=venue_id)
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
