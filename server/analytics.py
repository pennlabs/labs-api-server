from flask import request, jsonify
from server import app, sqldb
from .models import User, Account, AnalyticsEvent
import json
import datetime


@app.route('/feed/analytics', methods=['POST'])
def send_analytics():
    try:
        user = User.get_user()
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    try:
        account = Account.get_account()
        account_id = account.id
    except ValueError:
        account_id = None

    data = request.get_json()
    events = list(data)

    for event_json in events:
        timestamp_str = event_json.get("timestamp")
        timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%f')
        type = event_json.get("cell_type")
        index = int(event_json.get("index"))
        post_id = event_json.get("id")
        flag = bool(event_json.get("is_interaction"))
        event = AnalyticsEvent(user=user.id, account_id=account_id, timestamp=timestamp, type=type, index=index, post_id=post_id, is_interaction=flag)
        sqldb.session.add(event)
    sqldb.session.commit()

    return jsonify({'success': True, "error": None})
