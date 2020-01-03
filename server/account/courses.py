import ast
import datetime

from flask import g, jsonify, request
from sqlalchemy import func, text

from server import app, sqldb
from server.auth import anonymous_auth
from server.models import Course, CourseAccount, CourseAnonymousID, CourseInstructor, CourseMeetingTime


@app.route('/account/courses', methods=['POST'])
def update_courses_endpoint():
    """ Add/Update the courses associated with the account """
    # json = request.get_json()
    # if json:
    #     try:
    #         account_id = json['account_id']
    #         account = Account.query.filter_by(id=account_id).first()

    #         if account is None:
    #             return jsonify({'error': 'Account not found.'}), 400

    #         courses = json.get('courses')
    #         if courses:
    #             add_courses(account, courses)

    #         return jsonify({'success': True})
    #     except KeyError as e:
    #         return jsonify({'error': str(e)}), 400
    # else:
    #     return jsonify({'error': 'JSON not passed'}), 400
    return jsonify({'success': True})


@app.route('/account/courses', methods=['GET'])
def get_courses_endpoint():
    """ Get the courses associated with the account """
#     account_id = request.args.get('account_id')
#     date = request.args.get('date')
#     weekday = request.args.get('weekday')
#     if account_id is None:
#         return jsonify({'error': 'Missing account_id field.'}), 400
#
#     account = Account.query.filter_by(id=account_id).first()
#     if account is None:
#         return jsonify({'error': 'Account not found.'}), 400
#
#     courses = get_courses(account, date, weekday, weekday is None)
    return jsonify({'courses': []})


@app.route('/account/courses/private/save', methods=['POST'])
@anonymous_auth
def save_anonymouss_courses():
    """ Anonymously saves a user's courses """
    json = request.get_json()
    courses = add_courses_to_db(json)
    add_courses_anonymously(g.anonymous_id, courses)

    return jsonify({'success': True})


@app.route('/account/courses/private/delete', methods=['POST'])
@anonymous_auth
def delete_anonymouss_courses():
    """ Delete anonymous courses associated with device key and/or password hash """
    CourseAnonymousID.query.filter_by(anonymous_id=g.anonymous_id).delete()
    sqldb.session.commit()

    return jsonify({'success': True})


def add_courses_anonymously(anonymous_id, courses):
    # Delete all courses associated with this account for this term
    terms = set([x.term for x in courses])
    for term in terms:
        # TODO: before deleting them, save the old schedule to a history table
        query = sqldb.session.query(CourseAnonymousID, Course).join(Course) \
            .filter(CourseAnonymousID.anonymous_id == anonymous_id) \
            .filter(Course.term == term) \
            .all()
        for ca, course in query:
            sqldb.session.delete(ca)

    for course in courses:
        ca = CourseAnonymousID(anonymous_id=anonymous_id, course_id=course.id)
        sqldb.session.add(ca)
    sqldb.session.commit()


def add_courses(account, course_json):
    courses = add_courses_to_db(course_json)
    add_courses_to_account(account, courses)


def add_courses_to_account(account, courses):
    # Delete all courses associated with this account for this term
    terms = set([x.term for x in courses])
    for term in terms:
        query = sqldb.session.query(CourseAccount, Course).join(Course) \
            .filter(CourseAccount.account_id == account.id) \
            .filter(Course.term == term) \
            .all()
        for ca, course in query:
            sqldb.session.delete(ca)

    for course in courses:
        ca = CourseAccount(account_id=account.id, course_id=course.id)
        sqldb.session.add(ca)
    sqldb.session.commit()


def add_courses_to_db(json_array):
    """ Adds courses to DB and returns a list of Course objects"""
    courses_in_db = []
    courses_not_in_db = []
    course_instructors = {}
    course_meetings_times = {}
    for json in json_array:
        term = json.get('term')
        name = json.get('name')
        dept = json.get('dept')
        code = json.get('code')
        section = json.get('section')
        building = json.get('building')
        room = json.get('room')
        weekdays = json.get('weekdays')
        start_date_str = json.get('start_date')
        end_date_str = json.get('end_date')
        start_time = json.get('start_time')
        end_time = json.get('end_time')
        instructors = json.get('instructors')
        meeting_times = json.get('meeting_times')

        try:
            meeting_times = ast.literal_eval(str(meeting_times))
        except ValueError:
            pass

        parameters = [term, name, dept, code, section, weekdays, start_time, end_time, instructors]
        if any(x is None for x in parameters):
            raise KeyError('Course parameter is missing')

        if start_date_str and end_date_str:
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            start_date = None
            end_date = None

            # Use the most common start and end dates for this term if they are not explicitly defined
            term_start_end_dates = sqldb.session.query(
                Course.start_date,
                Course.end_date,
                func.count(Course.id).label('count')
            ) \
                .filter_by(term=term) \
                .group_by(Course.start_date, Course.end_date) \
                .order_by(text('count DESC')) \
                .all()

            if len(term_start_end_dates) > 0:
                start_date = term_start_end_dates[0][0]
                end_date = term_start_end_dates[0][1]

        course = Course.query.filter_by(dept=dept, code=code, section=section, term=term).first()
        if course:
            # If start/end date field was null or different, add the start/end date
            if course.start_date != start_date or course.end_date != end_date or course.building != building or (
               course.room != room):
                course.start_date = start_date
                course.end_date = end_date
                course.building = building
                course.room = room
                sqldb.session.commit()
            courses_in_db.append(course)
        if course is None:
            identifier = '{}{}{}{}'.format(term, dept, code, section)
            course_instructors[identifier] = instructors
            course_meetings_times[identifier] = meeting_times
            course = Course(term=term, name=name, dept=dept, code=code, section=section, building=building, room=room,
                            weekdays=weekdays, start_date=start_date, end_date=end_date, start_time=start_time,
                            end_time=end_time)
            sqldb.session.add(course)
            sqldb.session.commit()

            courses_not_in_db.append(course)

    if courses_not_in_db:
        for course in courses_not_in_db:
            identifier = '{}{}{}{}'.format(course.term, course.dept, course.code, course.section)
            instructors = course_instructors.get(identifier)
            if instructors:
                for instructor in instructors:
                    cp = CourseInstructor(course_id=course.id, name=instructor)
                    sqldb.session.add(cp)
            meeting_times = course_meetings_times.get(identifier)
            add_meeting_times(course, meeting_times)
        courses_in_db.extend(courses_not_in_db)

    return courses_in_db


def add_meeting_times(course, meeting_times_json):
    if meeting_times_json:
        if type(meeting_times_json) is not list:
            raise KeyError('Meeting times json is not a list.')

        for json in meeting_times_json:
            if type(json) is not dict:
                raise KeyError('Meeting time json is not a dictionary.')

            building = json.get('building')
            room = json.get('room')
            weekday = json.get('weekday')
            start_time = json.get('start_time')
            end_time = json.get('end_time')

            parameters = [weekday, start_time, end_time]
            if any(x is None for x in parameters):
                raise KeyError('Meeting time parameter is missing')

            if course.start_time != start_time or course.end_time != end_time or weekday not in course.weekdays:
                # Add flag to indicate that you need to lookup meeting times in the CourseMeetingTime table
                course.extra_meetings_flag = True

            meeting = CourseMeetingTime(course_id=course.id, weekday=weekday, start_time=start_time, end_time=end_time,
                                        building=building, room=room)
            sqldb.session.add(meeting)


def get_courses(account, day=None, weekday=None, include_extra_meeting_times=False):
    json_array = []     # Final json array to be returned
    courses = []        # All Courses. If weekday is not None, only ourses that do not have an extra_meetings_flag
    course_ids = []     # All course IDs. Used to get instructors.
    if day and weekday:
        # Get currently enrolled courses that are meeting today
        # First, get all currently enrolled courses
        course_query = sqldb.session.query(CourseAccount, Course).join(Course) \
            .filter(CourseAccount.account_id == account.id) \
            .filter(Course.end_date >= day) \
            .filter(Course.start_date <= day)
        courses_this_term = [course for (ca, course) in course_query]
        for course in courses_this_term:
            # Check if need to lookup extra meeetings in CourseMeetingTime Table
            if course.extra_meetings_flag:
                meetings = CourseMeetingTime.query.filter_by(course_id=course.id, weekday=weekday)
                for meeting in meetings:
                    course_ids.append(course.id)
                    # Add this meeting time to the JSON (may be more than one meeting time in a day for a class)
                    json_array.append({
                        'term': course.term,
                        'name': course.name,
                        'dept': course.dept,
                        'code': course.code,
                        'section': course.section,
                        'building': meeting.building,
                        'room': meeting.room,
                        'weekdays': meeting.weekday,
                        'start_date': course.start_date.strftime('%Y-%m-%d'),
                        'end_date': course.end_date.strftime('%Y-%m-%d'),
                        'start_time': meeting.start_time,
                        'end_time': meeting.end_time
                    })
            elif weekday in course.weekdays:
                # Add this course to the courses array to be processed later
                courses.append(course)
    elif day:
        # Get courses for this account that they are currently enrolled in
        course_query = sqldb.session.query(CourseAccount, Course).join(Course) \
            .filter(CourseAccount.account_id == account.id) \
            .filter(Course.end_date >= day) \
            .filter(Course.start_date <= day)
        courses = [course for (ca, course) in course_query]
    else:
        # Get all courses for this account
        course_query = sqldb.session.query(CourseAccount, Course).join(Course) \
            .filter(CourseAccount.account_id == account.id)
        courses = [course for (ca, course) in course_query]

    # Query for instructors based on course id
    course_ids.extend([course.id for course in courses])
    instructor_query = sqldb.session.query(Course, CourseInstructor).join(CourseInstructor) \
        .filter(CourseInstructor.course_id.in_(course_ids))

    # Iterate through each instructor in query and add them to appropriate class
    course_instructor_dict = {}
    for course, instructor in instructor_query:
        identifier = '{}{}{}{}'.format(course.term, course.dept, course.code, course.section)
        instructor_arr = course_instructor_dict.get(identifier)
        if instructor_arr:
            instructor_arr.append(instructor.name)
        else:
            course_instructor_dict[identifier] = [instructor.name]

    meeting_times_dict = {}
    if include_extra_meeting_times:
        # Iterate through each course and add its extra meetings times to the class
        for course in courses:
            identifier = '{}{}{}{}'.format(course.term, course.dept, course.code, course.section)
            meetings = CourseMeetingTime.query.filter_by(course_id=course.id)
            meetings_json_array = []
            for meeting in meetings:
                meetings_json_array.append({
                    'weekday': meeting.weekday,
                    'start_time': meeting.start_time,
                    'end_time': meeting.end_time,
                    'building': meeting.building,
                    'room': meeting.room
                })
            meeting_times_dict[identifier] = meetings_json_array

    for json in json_array:
        identifier = '{}{}{}{}'.format(json['term'], json['dept'], json['code'], json['section'])
        json['instructors'] = course_instructor_dict.get(identifier)

    for course in courses:
        identifier = '{}{}{}{}'.format(course.term, course.dept, course.code, course.section)
        json_array.append({
            'term': course.term,
            'name': course.name,
            'dept': course.dept,
            'code': course.code,
            'section': course.section,
            'building': course.building,
            'room': course.room,
            'weekdays': course.weekdays,
            'start_date': course.start_date.strftime('%Y-%m-%d'),
            'end_date': course.end_date.strftime('%Y-%m-%d'),
            'start_time': course.start_time,
            'end_time': course.end_time,
            'instructors': course_instructor_dict.get(identifier),
            'meeting_times': meeting_times_dict.get(identifier)
        })
    return json_array


def get_current_term_courses(account):
    now = datetime.datetime.now()
    now_str = now.strftime('%Y-%m-%d')
    return get_courses(account, now_str)


def get_todays_courses(account):
    return get_courses_in_N_days(account, 0)


def get_courses_in_N_days(account, inDays):
    now = datetime.datetime.now()
    today = now.strftime('%Y-%m-%d')
    weekday_array = ['S', 'M', 'T', 'W', 'R', 'F', 'S']
    weekday = weekday_array[(int(now.strftime('%w')) + inDays) % 7]
    return get_courses(account, today, weekday)
