import os
from datetime import datetime
from functools import wraps

import requests
from flask import g, jsonify, request
from sqlalchemy import or_

from server import sqldb
from server.models import Account, generate_uuid


def auth(nullable=False):
    def _auth(f):
        @wraps(f)
        def __auth(*args, **kwargs):
            # Authorization headers are restricted on iOS and not allowed to be set.
            # Thus, iOS sets an X-Authorization header to carry the bearer token.
            # We check both the X-Authorization header and the regular Authorization header for the access token.
            # For more info: see https://developer.apple.com/documentation/foundation/nsurlrequest#1776617
            g.account = None
            x_authorization = request.headers.get("X-Authorization")
            authorization = request.headers.get("Authorization")
            if (authorization and " " in authorization) or (
                x_authorization and " " in x_authorization
            ):
                auth_type, token = (
                    authorization.split() if authorization else x_authorization.split()
                )
                if auth_type == "Bearer":  # Only validate if Authorization header type is Bearer
                    try:
                        body = {"token": token}
                        headers = {"Authorization": "Bearer {}".format(token)}
                        data = requests.post(
                            url="https://platform.pennlabs.org/accounts/introspect/",
                            headers=headers,
                            data=body,
                        )
                        if data.status_code == 200:  # Access token is valid
                            data = data.json()
                            account = Account.query.filter_by(pennid=data["user"]["pennid"]).first()
                            if account:
                                g.account = account
                                return f()
                            else:
                                return (
                                    f()
                                    if nullable
                                    else (jsonify({"error": "Account not found."}), 400)
                                )
                        else:
                            return f() if nullable else (jsonify({"error": "Invalid token"}), 401)
                    except requests.exceptions.RequestException:  # Can't connect to platform
                        # Throw a 403 because we can't verify the incoming access token so we
                        # treat it as invalid. Ideally platform will never go down, so this
                        # should never happen.
                        return (
                            f()
                            if nullable
                            else (jsonify({"error": "Unable to connect to Platform"}), 401)
                        )
                else:
                    return (
                        f()
                        if nullable
                        else (jsonify({"error": "Authorization token type is not Bearer."}), 401)
                    )
            else:
                return (
                    f()
                    if nullable
                    else (jsonify({"error": "An access token was not provided."}), 401)
                )

        return __auth

    return _auth


def internal_auth(f):
    @wraps(f)
    def _internal_auth(*args, **kwargs):
        authorization = request.headers.get("Authorization")
        if authorization and " " in authorization:
            auth_type, token = authorization.split()
            if auth_type == "Bearer" and token == os.environ.get("AUTH_SECRET"):
                return f()
            else:
                return jsonify({"error": "Auth secret is not correct."}), 401
        else:
            return jsonify({"error": "Auth secret not provided."}), 401

    return _internal_auth


class AnonymousID(sqldb.Model):
    __tablename__ = "anonymous_id"

    id = sqldb.Column(sqldb.VARCHAR(255), primary_key=True, default=generate_uuid)
    device_key = sqldb.Column(sqldb.VARCHAR(255))
    password_hash = sqldb.Column(sqldb.VARCHAR(255))
    type = sqldb.Column(sqldb.VARCHAR(255))
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())
    updated_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())


def anonymous_auth(f):
    @wraps(f)
    def _anonymous_auth(*args, **kwargs):
        device_key = request.headers.get("X-Device-Key")
        password_hash = request.headers.get("X-Password-Hash")
        data_type = request.headers.get("X-Data-Type")

        if not device_key or not password_hash or not data_type:
            return (
                jsonify(
                    {"error": "Missing header X-Device-Key or X-Password-Hash or X-Data-Type."}
                ),
                400,
            )

        anonymous_id = (
            AnonymousID.query.filter(AnonymousID.type == data_type)
            .filter(
                or_(
                    AnonymousID.password_hash == password_hash, AnonymousID.device_key == device_key
                )
            )
            .first()
        )
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
            anonymous_id = AnonymousID(
                device_key=device_key, password_hash=password_hash, type=data_type
            )
            sqldb.session.add(anonymous_id)
            sqldb.session.commit()

        g.anonymous_id = anonymous_id.id
        return f()

    return _anonymous_auth
