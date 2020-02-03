import csv
import json
import os

import redis

from server import app


db = redis.StrictRedis().from_url(app.config['REDIS_URL'])
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'diningImages.csv')) as f:
    reader = csv.DictReader(f)
    for row in reader:
        db.set('venue:%s' % (row['id']), json.dumps(row['imageURL']))
