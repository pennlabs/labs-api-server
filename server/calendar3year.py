from flask import jsonify
from .penndata import calendar
from server import app
import datetime


def pull_calendar(d):
    """Pulls the calendar from the Penn website and
    filters out which events are 2 weeks away from date d.

    :param d: date object that specifies the date
    """
    pulled_calendar = calendar.pull_3year()
    within_range = []
    for event in pulled_calendar:
        start = event['start']
        event_date = datetime.datetime.strptime(start, '%Y-%m-%d').date()
        time_diff = event_date - d
        if time_diff.total_seconds() > 0 and time_diff.total_seconds() <= 1209600:
            within_range.append(event)
    return jsonify({'calendar': within_range})


@app.route('/calendar', methods=['GET'])
def pull_today():
    """Returns JSON object with all events 2 weeks from the
    current date.
    """
    today = datetime.datetime.now().date()
    return pull_calendar(today)


@app.route('/calendar/<date>', methods=['GET'])
def pull_date(date):
    """Return JSON object with all events 2 weeks from the
    date passed in as an argument.
    """
    d = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    return pull_calendar(d)
