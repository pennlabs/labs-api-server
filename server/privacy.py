from datetime import datetime

from flask import g, jsonify, request
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from server import app, sqldb
from server.auth import auth
from server.models import generate_uuid


class PrivacySetting(sqldb.Model):
    account = sqldb.Column(sqldb.VARCHAR(255), sqldb.ForeignKey('account.id'), primary_key=True)
    setting = sqldb.Column(sqldb.VARCHAR(255), primary_key=True)
    enabled = sqldb.Column(sqldb.Boolean)
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())
    updated_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())


class AnonymousID(sqldb.Model):
    __tablename__ = 'anonymous_id'

    id = sqldb.Column(sqldb.VARCHAR(255), primary_key=True, default=generate_uuid)
    device = sqldb.Column(sqldb.VARCHAR(255))
    password_hash = sqldb.Column(sqldb.VARCHAR(255))
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())
    updated_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())


@app.route('/privacy/settings', methods=['POST'])
@auth()
def save_privacy_settings():
    settings = request.get_json()
    for setting in settings:
        enabled = settings[setting]
        privSetting = PrivacySetting(account=g.account.id, setting=setting, enabled=enabled)
        try:
            sqldb.session.add(privSetting)
            sqldb.session.commit()
        except IntegrityError:
            sqldb.session.rollback()
            privSetting = PrivacySetting.query.filter_by(account=g.account.id, setting=setting).first()
            if privSetting.enabled != enabled:
                privSetting.enabled = enabled
                privSetting.updated_at = datetime.now()
                sqldb.session.commit()
    return jsonify({'success': True})


@app.route('/privacy/settings', methods=['GET'])
@auth()
def get_privacy_settings_endpoint():
    jsonArr = get_privacy_settings(g.account)
    return jsonify({'settings': jsonArr})


def get_privacy_settings(account):
    settings = PrivacySetting.query.filter_by(account=account.id).all()
    jsonArr = {}
    for setting in settings:
        jsonArr[setting.setting] = setting.enabled
    return jsonArr


def get_anonymous_id(device_key, password_hash):
    anonymous_id = AnonymousID.query.filter(or_(AnonymousID.password_hash == password_hash,
                                                AnonymousID.device_key == device_key)).first()
    if anonymous_id:
        # If device key or password hash has changed, update them
        if anonymous_id.device_key != device_key:
            anonymous_id.device_key = device_key
            anonymous_id.updated_at = datetime.now()
            sqldb.session.commit()
        elif anonymous_id.password_hash != password_hash:
            anonymous_id.password_hash = password_hash
            anonymous_id.updated_at = datetime.now()
            sqldb.session.commit()
    else:
        anonymous_id = AnonymousID(device_key=device_key, password_hash=password_hash)
        sqldb.session.add(anonymous_id)
        sqldb.session.commit()

    return anonymous_id.id
