import os
from datetime import datetime

from apns2.client import APNsClient
from apns2.credentials import TokenCredentials
from apns2.payload import Payload
from flask import g, jsonify, request
from sqlalchemy.exc import IntegrityError

from server import app, sqldb
from server.auth import auth, internal_auth
from server.models import Account


class NotificationToken(sqldb.Model):
    account = sqldb.Column(sqldb.VARCHAR(255), sqldb.ForeignKey("account.id"), primary_key=True)
    ios_token = sqldb.Column(sqldb.VARCHAR(255), nullable=True)
    android_token = sqldb.Column(sqldb.VARCHAR(255), nullable=True)
    dev = sqldb.Column(sqldb.Boolean, default=False)
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())
    updated_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())


class NotificationSetting(sqldb.Model):
    account = sqldb.Column(sqldb.VARCHAR(255), sqldb.ForeignKey("account.id"), primary_key=True)
    setting = sqldb.Column(sqldb.VARCHAR(255), primary_key=True)
    enabled = sqldb.Column(sqldb.Boolean)
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())
    updated_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())


class Notification(object):
    def __init__(self, token, payload):
        self.token = token
        self.payload = payload


@app.route("/notifications/register", methods=["POST"])
@auth()
def register_push_notification():
    ios_token = request.form.get("ios_token")
    android_token = request.form.get("android_token")
    isDev = True if request.form.get("dev") else False

    notification_token = NotificationToken(
        account=g.account.id, ios_token=ios_token, android_token=android_token, dev=isDev
    )

    try:
        sqldb.session.add(notification_token)
        sqldb.session.commit()
    except IntegrityError:
        sqldb.session.rollback()
        current_result = NotificationToken.query.filter_by(account=g.account.id).first()
        if current_result:
            current_result.ios_token = ios_token
            current_result.android_token = android_token
            current_result.dev = isDev
            current_result.updated_at = datetime.now()
            sqldb.session.commit()

    return jsonify({"registered": True})


@app.route("/notifications/send", methods=["POST"])
@auth()
def send_push_notification_to_account():
    title = request.form.get("title")
    body = request.form.get("body")
    token = NotificationToken.query.filter_by(account=g.account.id).first()

    if not token or not token.ios_token:
        return jsonify({"error": "A device token has not been registered on the server."}), 400

    send_push_notification(token.ios_token, title, body, token.dev)
    return jsonify({"success": True})


@app.route("/notifications/send/internal", methods=["POST"])
@internal_auth
def send_test_push_notification():
    pennkey = request.form.get("pennkey")
    title = request.form.get("title")
    body = request.form.get("body")
    if not pennkey:
        return jsonify({"error": "Missing pennkey."}), 400

    account = Account.query.filter_by(pennkey=pennkey).first()
    if not account:
        return jsonify({"error": "Account not found."}), 400

    token = NotificationToken.query.filter_by(account=account.id).first()

    if not token or not token.ios_token:
        return (
            jsonify(
                {"error": "A device token has not been registered on the server for this account."}
            ),
            400,
        )

    # Only development tokens can be tested (not production)
    send_push_notification(token.ios_token, title, body, token.dev)
    return jsonify({"success": True})


@app.route("/notifications/send/token/internal", methods=["POST"])
@internal_auth
def send_test_push_notification_with_token():
    token = request.form.get("token")
    title = request.form.get("title")
    body = request.form.get("body")
    if not token:
        return jsonify({"error": "Missing token."}), 400

    if not token:
        return (
            jsonify(
                {"error": "A device token has not been registered on the server for this account."}
            ),
            400,
        )

    # Only development tokens can be tested (not production)
    send_push_notification(token, title, body, True)
    return jsonify({"success": True})


def send_push_notification(token, title, body, isDev=False):
    client = get_client(isDev)
    alert = {"title": title, "body": body}
    payload = Payload(alert=alert, sound="default", badge=0)
    topic = "org.pennlabs.PennMobile"
    client.send_notification(token, payload, topic)


def send_push_notification_batch(notifications, isDev=False):
    client = get_client(isDev)
    topic = "org.pennlabs.PennMobile"
    client.send_notification_batch(notifications=notifications, topic=topic)


def get_client(isDev):
    auth_key_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ios_key.p8"
    )
    auth_key_id = "443RV92X4F"
    team_id = "VU59R57FGM"
    token_credentials = TokenCredentials(
        auth_key_path=auth_key_path, auth_key_id=auth_key_id, team_id=team_id
    )
    client = APNsClient(credentials=token_credentials, use_sandbox=isDev)
    return client


""" Notification Settings """


@app.route("/notifications/settings", methods=["POST"])
@auth()
def save_notification_settings():
    settings = request.get_json()
    for setting in settings:
        enabled = settings[setting]
        notifSetting = NotificationSetting(account=g.account.id, setting=setting, enabled=enabled)
        try:
            sqldb.session.add(notifSetting)
            sqldb.session.commit()
        except IntegrityError:
            sqldb.session.rollback()
            notifSetting = NotificationSetting.query.filter_by(
                account=g.account.id, setting=setting
            ).first()
            if notifSetting.enabled != enabled:
                notifSetting.enabled = enabled
                notifSetting.updated_at = datetime.now()
                sqldb.session.commit()
    return jsonify({"success": True})


@app.route("/notifications/settings", methods=["GET"])
@auth()
def get_notification_settings_endpoint():
    jsonArr = get_notification_settings(g.account)
    return jsonify({"settings": jsonArr})


def get_notification_settings(account):
    settings = NotificationSetting.query.filter_by(account=account.id).all()
    jsonArr = {}
    for setting in settings:
        jsonArr[setting.setting] = setting.enabled
    return jsonArr
