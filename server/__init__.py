from flask import Flask
from server.models import sqldb
from apscheduler.schedulers.background import BackgroundScheduler
import os
import redis

app = Flask(__name__)

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

# scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(server.laundry.save_data, 'interval', minutes=15)
scheduler.start()

if __name__ == '__main__':
    app.run(debug=True)
