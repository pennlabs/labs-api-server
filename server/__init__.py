from flask import Flask, session, jsonify, Response, request, json, render_template, redirect, current_app
import pymongo
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# mongo
client = pymongo.MongoClient()
db = client['registrar']
app.secret_key = os.urandom(24)
import server.api


if __name__ == '__main__':
    app.run(debug=True)
