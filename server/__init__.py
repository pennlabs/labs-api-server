import os

import boto3
import redis
import tinify
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from raven.contrib.flask import Sentry

from server.models import sqldb


app = Flask(__name__)
bcrypt = Bcrypt(app)

# Tinify Image Compression API
tinify.key = os.environ.get("TINIFY_KEY")

# sentry
sentry = Sentry(app)

# AWS S3
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.environ.get("AWS_KEY"),
    aws_secret_access_key=os.environ.get("AWS_SECRET"),
)

# allow cors
CORS(app)

# redis
app.config["REDIS_URL"] = os.environ.get("REDIS_URL", "redis://localhost:6379")
db = redis.StrictRedis().from_url(app.config["REDIS_URL"])
app.secret_key = os.urandom(24)

import server.account.account  # noqa
import server.account.settings  # noqa
import server.analytics  # noqa
import server.auth  # noqa
import server.buildings  # noqa
import server.calendar3year  # noqa
import server.dining.balance  # noqa
import server.dining.diningRedis  # noqa
import server.dining.hours_menus  # noqa
import server.dining.preferences  # noqa
import server.dining.transactions  # noqa
import server.directory  # noqa
import server.event  # noqa
import server.fitness  # noqa
import server.homepage  # noqa
import server.laundry  # noqa
import server.news  # noqa
import server.nso  # noqa
import server.pcr  # noqa
import server.polls.archive  # noqa
import server.polls.creation  # noqa
import server.polls.vote  # noqa
import server.portal.account  # noqa
import server.portal.creation  # noqa
import server.portal.posts  # noqa
import server.registrar  # noqa
import server.studyspaces.availability  # noqa
import server.studyspaces.book  # noqa
import server.studyspaces.cancel  # noqa
import server.studyspaces.deprecated  # noqa
import server.studyspaces.notifications  # noqa
import server.studyspaces.reservations  # noqa
import server.studyspaces.search  # noqa
import server.transit  # noqa
import server.weather  # noqa
import server.housing  # noqa
import server.notifications  # noqa
import server.privacy  # noqa

# sql
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///:memory:")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
sqldb.init_app(app)
with app.app_context():
    sqldb.create_all()

if __name__ == "__main__":
    app.run(debug=True)
