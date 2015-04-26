from server import app, db
from functools import wraps
from flask import request, Response
import hashlib
from os import urandom

@app.route('/auth', methods=['GET'])
def auth():
  authInfo = None
  print request.cookies
  for key, val in request.cookies.items():
    if '_shibsession_' in key:
      authInfo = key + val
      break
  print authInfo
  if authInfo:
    authToken = hashlib.pbkdf2_hmac('sha256', authInfo, urandom(), 100000)
    print authToken
    db.set('authToken:%s' % authToken);
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
