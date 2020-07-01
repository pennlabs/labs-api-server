import datetime
import json

from flask import jsonify, make_response

from server import db


def cached_route(redis_key, td, func):
    data = cache_get(redis_key, td, func)
    secs = int(db.ttl(redis_key))
    return make_response(jsonify(data), 200, {"Cache-Control": "max-age=%d" % secs})


def cache_get(redis_key, td, func):
    if db.exists(redis_key):
        return json.loads(db.get(redis_key).decode("utf8"))
    else:
        data = func()
        db.set(redis_key, json.dumps(data))
        db.pexpireat(redis_key, datetime.datetime.now() + td)
        return data
