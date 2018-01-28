import penncoursereview as pcr
from collections import defaultdict
import datetime
from .base import cached_route
from server import app


def course_reviews(course_id):
    history = pcr.CourseHistory(course_id)
    return pcr.penncoursereview.fetch_pcr(history.reviews.path)


def average_course_review(course_id):
    reviews = course_reviews(course_id)['values']
    total = defaultdict(int)
    for review in reviews:
        for rating in review['ratings']:
            total[rating] += float(review['ratings'][rating])
    for rating in total:
        total[rating] /= len(reviews)
    return total


@app.route('/pcr/<course_id>', methods=['GET'])
def get_course_reviews(course_id):
    now = datetime.datetime.today()
    end_day = datetime.datetime(now.year, now.month, now.day) + \
        datetime.timedelta(days=15)
    td = end_day - now

    def get_data():
        return average_course_review(course_id)
    return cached_route('pcr:course:%s' % course_id, td, get_data)
