import os
import redis
import tinify
import boto3

from flask import Flask
from flask_cors import CORS
from raven.contrib.flask import Sentry
from server.models import sqldb
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)

# Tinify Image Compression API
tinify.key = os.environ.get("TINIFY_KEY")

# sentry
sentry = Sentry(app)

# AWS S3
s3 = boto3.client(
    's3',
    aws_access_key_id=os.environ.get("AWS_KEY"),
    aws_secret_access_key=os.environ.get("AWS_SECRET"),
)

# allow cors
CORS(app)

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
import server.dining.dining
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
import server.fitness
import server.homepage
import server.news
import server.account
import server.analytics
import server.portal

if __name__ == '__main__':
    app.run(debug=True)
