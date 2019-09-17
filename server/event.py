import pytz
from flask import jsonify

from . import app
from .models import Event


utc = pytz.timezone('UTC')
eastern = pytz.timezone('US/Eastern')


@app.route('/events/<type>', methods=['GET'])
def get_events(type):
    events = Event.query.filter_by(type=type)

    events_dict = [{
        'name': x.name,
        'description': x.description,
        'image_url': x.image_url,
        'start_time': utc.localize(x.start_time).astimezone(eastern).isoformat(),
        'end_time': utc.localize(x.end_time).astimezone(eastern).isoformat(),
        'email': x.email,
        'website': x.website,
        'facebook': x.facebook
    } for x in events]

    return jsonify({'events': events_dict})
