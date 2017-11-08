import datetime
import calendar

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


def safe_division(a, b):
    return round(a / float(b), 3) if b > 0 else 0


@app.route('/laundry/graph/<int:hall_no>', methods=['GET'])
def graph(hall_no):
    now = datetime.datetime.now()
    start = now.date() - datetime.timedelta(days=30)
    # python dow is monday = 0, while sql dow is sunday = 0
    dow = (now.today().weekday() + 1) % 7
    tmw = (dow + 1) % 7
    # get the laundry information for today based on the day
    # of week (if today is tuesday, get all the tuesdays
    # in the past 30 days), group them by time, and include
    # the first 2 hours of the next day
    data = sqldb.session.query(
        LaundrySnapshot.date,
        LaundrySnapshot.time,
        func.sum(LaundrySnapshot.washers).label("all_washers"),
        func.sum(LaundrySnapshot.dryers).label("all_dryers"),
        func.sum(LaundrySnapshot.total_washers).label("all_total_washers"),
        func.sum(LaundrySnapshot.total_dryers).label("all_total_dryers"),
    ).filter((LaundrySnapshot.room == hall_no) &
             ((func.strftime("%w", LaundrySnapshot.date) == str(dow)) |
              ((LaundrySnapshot.time <= 180 - 1) &
               (func.strftime("%w", LaundrySnapshot.date) == str(tmw)))) &
             (LaundrySnapshot.date >= start)) \
     .group_by(LaundrySnapshot.date, LaundrySnapshot.time) \
     .order_by(LaundrySnapshot.date, LaundrySnapshot.time).all()
    data = [x._asdict() for x in data]
    all_dryers = [x["all_total_dryers"] for x in data]
    all_washers = [x["all_total_washers"] for x in data]
    washer_points = {k: 0 for k in range(27)}
    dryer_points = {k: 0 for k in range(27)}
    washer_total = {k: 0 for k in range(27)}
    dryer_total = {k: 0 for k in range(27)}
    for x in data:
        hour = int(x["time"] / 60)
        # if the value is for tomorrow, add 24 hours
        if x["date"].weekday() == dow:
            hour += 24
        washer_points[hour] += x["all_washers"]
        dryer_points[hour] += x["all_dryers"]
        washer_total[hour] += 1
        dryer_total[hour] += 1
    return jsonify({
        "hall_name": laundry.id_to_hall[hall_no],
        "location": laundry.id_to_location[hall_no],
        "day_of_week": calendar.day_name[now.today().weekday()],
        "start_date": start.strftime("%m-%d-%y"),
        "end_date": now.strftime("%m-%d-%y"),
        "number_of_dryers": safe_division(sum(all_dryers), len(all_dryers)),
        "number_of_washers": safe_division(sum(all_washers), len(all_washers)),
        "washer_data": {x: safe_division(washer_points[x], washer_total[x]) for x in washer_points},
        "dryer_data": {x: safe_division(dryer_points[x], dryer_total[x]) for x in dryer_points}
    })


def save_data():
    now = datetime.datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    date = now.date()
    time = round((now - midnight).seconds / 60)

    # check if we already have data for this minute
    # if we do, skip
    with app.app_context():
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
