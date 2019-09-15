import redis
import json
import csv

db = redis.StrictRedis(host='localhost', port=6379, db=0)
with open('diningImages.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        db.set("venue:%s" % (row["id"]), json.dumps(row["imageUrl"]))
