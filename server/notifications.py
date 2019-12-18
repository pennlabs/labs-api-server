from datetime import datetime

from flask import jsonify, request
from sqlalchemy.exc import IntegrityError

from server import app, sqldb
from server.auth import auth


class NotificationToken(sqldb.Model):
    account = sqldb.Column(sqldb.VARCHAR(255), sqldb.ForeignKey('account.id'), primary_key=True)
    ios_token = sqldb.Column(sqldb.VARCHAR(255), nullable=True)
    android_token = sqldb.Column(sqldb.VARCHAR(255), nullable=True)
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())
    updated_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())


@app.route('/notifications/register', methods=['POST'])
@auth()
def register_push_notification(account):
    ios_token = request.form.get('ios_token')
    android_token = request.form.get('android_token')

    notification_token = NotificationToken(account=account.id, ios_token=ios_token, android_token=android_token)

    try:
        sqldb.session.add(notification_token)
        sqldb.session.commit()
    except IntegrityError:
        sqldb.session.rollback()
        current_result = NotificationToken.query.filter_by(account=account.id).first()
        if current_result:
            current_result.ios_token = ios_token
            current_result.android_token = android_token
            current_result.updated_at = datetime.now()
            sqldb.session.commit()

    return jsonify({'registered': True})


@app.route('/notifications/send', methods=['POST'])
@auth()
def register_push_notification(account):
    token = NotificationToken.query.filter_by(account=account.id).first()

    if not token.ios_token:
        return jsonify({'error': 'A device token has not been registered'}), 400

	print(token.ios_token)
	return jsonify({'success': True})		
