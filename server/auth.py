import os
from server import app, db
from functools import wraps
from flask import request, Response, jsonify
import hashlib
import binascii

from .models import User


def json_status(json, status_code=None):
    resp = jsonify(json)
    if status_code:
        resp.status_code = status_code
    return resp


@app.route('/device/register', methods=['POST'])
def register_user():
    secret = os.environ.get('AUTH_SECRET')
    auth_secret = request.form.get("auth_secret")
    if auth_secret is None:
        return Response(response="Auth secret is not provided", status=400)
    if not (auth_secret == secret):
        return Response(response="Auth secret is not correct.", status=400)

    try:
        User.get_or_create()
        return jsonify({'exists': True})
    except ValueError as err:
        return Response(response=str(err), status=400)


@app.route('/auth', methods=['GET'])
def auth():
    authInfo = None
    for key, val in request.cookies.items():
        if '_shibsession_' in key:
            authInfo = key + val
            break
    if authInfo:
        # Convert to bytes for Python 3, assume always ASCII
        auth_info = bytearray(authInfo, 'ascii')
        # Salt is not necessary since we are hashing a session token
        hmac_token = hashlib.pbkdf2_hmac('sha256', auth_info, b'salt', 100000)
        authToken = binascii.hexlify(hmac_token)
        db.set('authToken:%s' % authToken, 1)
        return authToken
    else:
        return Response(response="no shibboleth cookie", status=400)


@app.route('/validate/<string:token>', methods=['GET'])
def validate(token):
    debug = app.debug or app.testing
    if not request.base_url.startswith('https') and not debug:
        return json_status({"status": "insecure access over http"}, 401)
    if db.exists('authToken:%s' % token):
        return json_status({"status": "valid"})
    else:
        return json_status({"status": "invalid"}, 401)


def auth_decorator(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        if db.exists('authToken:%s' % request.args['authToken']):
            return f(*args, **kwds)
        else:
            return Response(status=401)

    return wrapper
