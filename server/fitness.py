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
