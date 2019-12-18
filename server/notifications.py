from datetime import datetime

from apns2.client import APNsClient
from apns2.credentials import TokenCredentials
from apns2.payload import Payload
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
def send_push_notification(account):
    title = request.form.get('title')
    body = request.form.get('body')
    token = NotificationToken.query.filter_by(account=account.id).first()
    use_sandbox = True if request.form.get('dev') else False

    if not token.ios_token:
        return jsonify({'error': 'A device token has not been registered on the server.'}), 400

    auth_key_path = 'ios_key.p8'
    auth_key_id = '6MBD9SUNGE'
    team_id = 'VU59R57FGM'
    token_credentials = TokenCredentials(auth_key_path=auth_key_path, auth_key_id=auth_key_id, team_id=team_id)
    client = APNsClient(credentials=token_credentials, use_sandbox=use_sandbox)

    alert = {'title': title, 'body': body}
    payload = Payload(alert=alert, sound="default", badge=1)
    topic = 'org.pennlabs.PennMobile'
    client.send_notification(token.ios_token, payload, topic)

    return jsonify({'success': True})
