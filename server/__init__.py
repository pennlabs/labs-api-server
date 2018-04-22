import os
import redis

from flask import Flask
from raven.contrib.flask import Sentry
from server.models import sqldb

app = Flask(__name__)

# sentry
sentry = Sentry(app)

# sql
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///:memory:")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
sqldb.init_app(app)
with app.app_context():
    sqldb.create_all()

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
import server.weather
import server.calendar3year
import server.event
# import server.fitness
import server.homepage

if __name__ == '__main__':
    app.run(debug=True)
