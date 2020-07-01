import datetime
import re

from flask import jsonify
from pytz import timezone

from server import app
from server.base import cache_get
from server.penndata import calendar


def pull_calendar(d):
    """Pulls the calendar from the Penn website and
    filters out which events are 2 weeks away from date d.

    :param d: date object that specifies the date
    """
    pulled_calendar = cache_get("calendar:3year", datetime.timedelta(weeks=1), calendar.pull_3year)
    within_range = []
    for event in pulled_calendar:
        start = event["end"]
        event_date = datetime.datetime.strptime(start, "%Y-%m-%d").date()
        time_diff = event_date - d
        if time_diff.total_seconds() > 0 and time_diff.total_seconds() <= 1209600:
            event["name"] = re.split(
                "Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday", event["name"]
            )[0].strip()
            event["name"] = re.split(r"\($", event["name"])[0].strip()
            event["name"] = event["name"].replace("\\", "")
            if "Advance Registration" in event["name"]:
                event["name"] = "Advance Registration"
            within_range.append(event)
    return within_range


def pull_calendar_response(d):
    calendar = pull_calendar(d)
    return jsonify({"calendar": calendar})


def pull_todays_calendar():
    """Returns array of events which are 2 weeks away
    from today
    """
    est = timezone("EST")
    now = datetime.datetime.now(est)
    today = now.date()
    return pull_calendar(today)


@app.route("/calendar/", methods=["GET"])
def pull_today():
    """Returns JSON object with all events 2 weeks from the
    current date.
    """
    est = timezone("EST")
    now = datetime.datetime.now(est)
    today = now.date()
    return pull_calendar_response(today)


@app.route("/calendar/<date>", methods=["GET"])
def pull_date(date):
    """Return JSON object with all events 2 weeks from the
    date passed in as an argument.
    """
    d = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    return pull_calendar_response(d)
