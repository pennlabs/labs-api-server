from flask import Flask
import os
import redis

app = Flask(__name__)

# redis
db = redis.StrictRedis(host='localhost', port=6379, db=0)
app.secret_key = os.urandom(24)

import server.registrar
import server.transit
import server.dining
import server.buildings
import server.directory
import server.laundry
import server.auth
import server.pcr
import server.athletics
import server.nso
import server.studyspaces

if __name__ == '__main__':
    app.run(debug=True)
