import csv
import json

import redis

from server import app


db = redis.StrictRedis().from_url(app.config['REDIS_URL'])
with open('buildings.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        db.set('buildings:%s' % (row['code_courses']), json.dumps(row))
