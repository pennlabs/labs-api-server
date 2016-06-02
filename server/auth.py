from server import app, db
from functools import wraps
from flask import request, Response
import hashlib
import binascii


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
    db.set('authToken:%s' % authToken, 1);
    return authToken
  else:
    return Response(response="no shibboleth cookie", status=400)


def auth_decorator(f):
  @wraps(f)
  def wrapper(*args, **kwds):
    if db.exists('authToken:%s' % request.args['authToken']):
      return f(*args, **kwds)
    else:
      return Response(status=401)
  return wrapper
