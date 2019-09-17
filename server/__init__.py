import os

import boto3
import redis
import tinify
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from raven.contrib.flask import Sentry

import server.account
import server.analytics
import server.athletics
import server.auth
import server.buildings
import server.calendar3year
import server.dining.balance
import server.dining.diningRedis
import server.dining.hours_menus
import server.dining.preferences
import server.dining.transactions
import server.directory
import server.event
import server.fitness
import server.homepage
import server.laundry
import server.news
import server.nso
import server.pcr
import server.portal.account
import server.portal.creation
import server.portal.posts
import server.registrar
import server.studyspaces.availability
import server.studyspaces.book
import server.studyspaces.cancel
import server.studyspaces.deprecated
import server.studyspaces.reservations
import server.transit
import server.weather
from server.models import sqldb


app = Flask(__name__)
bcrypt = Bcrypt(app)

# Tinify Image Compression API
tinify.key = os.environ.get('TINIFY_KEY')

# sentry
sentry = Sentry(app)

# AWS S3
s3 = boto3.client(
    's3',
    aws_access_key_id=os.environ.get('AWS_KEY'),
    aws_secret_access_key=os.environ.get('AWS_SECRET'),
)

# allow cors
CORS(app)

# sql
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///:memory:')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
sqldb.init_app(app)
with app.app_context():
    sqldb.create_all()

# redis
db = redis.StrictRedis(host='localhost', port=6379, db=0)
app.secret_key = os.urandom(24)


if __name__ == '__main__':
    app.run(debug=True)
