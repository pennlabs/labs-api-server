import datetime

from server import app
from .penndata import fitness
from .base import cached_route


@app.route('/fitness/usage', methods=['GET'])
def fitness_usage():
    def get_data():
        return {"results": fitness.get_usage()}

    td = datetime.timedelta(minutes=30)
    return cached_route('fitness:usage', td, get_data)


@app.route('/fitness/schedule', methods=['GET'])
def fitness_schedule():
    def get_data():
        return {"schedule": fitness.get_schedule()}

    td = datetime.timedelta(hours=1)
    return cached_route('fitness:schedule', td, get_data)
