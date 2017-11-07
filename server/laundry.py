import datetime

from flask import jsonify
from server import app, sqldb
from server.models import LaundrySnapshot
from sqlalchemy import func, exists
from .penndata import laundry
from requests.exceptions import HTTPError


@app.route('/laundry/halls', methods=['GET'])
def all_halls():
    try:
        return jsonify({"halls": laundry.all_status()})
    except HTTPError:
        return jsonify({'error': 'The laundry api is currently unavailable.'})


@app.route('/laundry/hall/<int:hall_id>', methods=['GET'])
def hall(hall_id):
    try:
        return jsonify(laundry.hall_status(hall_id))
    except ValueError:
        return jsonify({'error': 'Invalid hall id passed to server.'})
    except HTTPError:
        return jsonify({'error': 'The laundry api is currently unavailable.'})


@app.route('/laundry/hall/<int:hall_id>/<int:hall_id2>', methods=['GET'])
def two_halls(hall_id, hall_id2):
    try:
        to_ret = {"halls": [laundry.hall_status(hall_id), laundry.hall_status(hall_id2)]}
        return jsonify(to_ret)
    except ValueError:
        return jsonify({'error': 'Invalid hall id passed to server.'})
    except HTTPError:
        return jsonify({'error': 'The laundry api is currently unavailable.'})


@app.route('/laundry/halls/ids', methods=['GET'])
def id_to_name():
    try:
        return jsonify({
            "halls": laundry.hall_id_list
        })
    except HTTPError:
        return jsonify({'error': 'The laundry api is currently unavailable.'})


@app.route('/laundry/usage/<int:hall_no>', methods=['GET'])
def usage(hall_no):
    days = laundry.machine_usage(hall_no)
    try:
        return jsonify({"days": days})
    except HTTPError:
        return jsonify({'error': 'The laundry api is currently unavailable.'})


@app.route('/laundry/graph/<int:hall_no>', methods=['GET'])
def graph(hall_no):
    save_data()
    now = datetime.datetime.now()
    # python dow is monday = 0, while sql dow is sunday = 0
    dow = (now.today().weekday() + 1) % 7
    data = sqldb.session.query(
        LaundrySnapshot.time,
        func.sum(LaundrySnapshot.washers).label("all_washers"),
        func.sum(LaundrySnapshot.dryers).label("all_dryers"),
        func.sum(LaundrySnapshot.total_washers).label("all_total_washers"),
        func.sum(LaundrySnapshot.total_dryers).label("all_total_dryers"),
    ).filter(LaundrySnapshot.room == hall_no,
             func.strftime("%w", LaundrySnapshot.date) == str(dow)) \
     .group_by(LaundrySnapshot.time) \
     .order_by(LaundrySnapshot.time).all()
    data = [x._asdict() for x in data]
    return jsonify({"result": data})


def save_data():
    now = datetime.datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    date = now.date()
    time = round((now - midnight).seconds / 60)

    # check if we already have data for this minute
    # if we do, skip
    if sqldb.session.query(exists().where((LaundrySnapshot.date == date) & (LaundrySnapshot.time == time))).scalar():
        return

    # make a dict for hall name -> id
    ids = {x["hall_name"]: x["id"] for x in laundry.hall_id_list}
    data = laundry.all_status()
    for name, room in data.items():
        id = ids[name]
        dryers = room["dryers"]["open"]
        washers = room["washers"]["open"]
        total_dryers = sum([room["dryers"][x] for x in ["offline", "open", "out_of_order", "running"]])
        total_washers = sum([room["washers"][x] for x in ["offline", "open", "out_of_order", "running"]])
        item = LaundrySnapshot(
            date=date,
            time=time,
            room=id,
            washers=washers,
            dryers=dryers,
            total_washers=total_washers,
            total_dryers=total_dryers
        )
        sqldb.session.add(item)
    sqldb.session.commit()
