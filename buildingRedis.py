import csv
import json

import redis


db = redis.StrictRedis(host='localhost', port=6379, db=0)
with open('buildings.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        db.set('buildings:%s' % (row['code_courses']), json.dumps(row))
