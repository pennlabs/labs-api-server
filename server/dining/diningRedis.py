import redis
import json
import csv
import os

# db = redis.StrictRedis(host='localhost', port=6379, db=0)
# with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'diningImages.csv')) as f:
#     reader = csv.DictReader(f)
#     for row in reader:
#         db.set("venue:%s" % (row["id"]), json.dumps(row["imageUrl"]))
