import redis
import json


db = redis.StrictRedis(host='localhost', port=6379, db=0)
with open('buildings.csv') as f:
  for line in f:
    arr = line.split(",")
    building = dict()
    building["name"] = arr[0]
    building["latitude"] = arr[1]
    building["longitude"] = arr[2]
    print "setting %s to %s" % (arr[4], json.dumps(building))
    db.set("buildings:%s" % (arr[4]), json.dumps(building))
