from flask import jsonify
from server import app
from penndata import *

@app.route('/laundry/halls', methods=['GET'])
def all_halls():
  return jsonify({"halls": laundry.all_status()})

@app.route('/laundry/hall/<hall_no>', methods=['GET'])
def hall(hall_no):
  return jsonify(laundry.hall_status(int(hall_no)))
