from server import app, db
from functools import wraps
from flask import request, Response
import hashlib, binascii

@app.route('/auth', methods=['GET'])
def auth():
  authInfo = None
  for key, val in request.cookies.items():
    if '_shibsession_' in key:
      authInfo = key + val
      break
  if authInfo:
    # Salt is not necessary since we are hashing a session token
    authToken = binascii.hexlify(hashlib.pbkdf2_hmac('sha256', authInfo, b'salt', 100000))
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
