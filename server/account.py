import requests
import datetime
import ast

from flask import jsonify, request

from server import app, db, sqldb
from .models import Account, School, Degree, Major, SchoolMajorAccount, Course, CourseAccount, CourseInstructor, CourseMeetingTime
from sqlalchemy.exc import IntegrityError


"""
Example: JSON Encoding
{
    "first": "Josh",
    "last": "Doman",
    "image_url": null,
    "pennkey": "joshdo",
    "degrees": [
        {
            "school_name": "Engineering & Applied Science",
            "school_code": "EAS",
            "degree_name":"Bachelor of Science in Economics",
            "degree_code":"BS",
            "expected_grad_term": "2020A",
            "majors": [
                {
                    "major_name": "Applied Science - Computer Science",
                    "major_code": "ASCS"
                }
            ]
        }, {
            "school_name": "Wharton Undergraduate",
            "school_code": "WH",
            "degree_name":"Bachelor of Applied Science",
            "degree_code":"BAS",
            "expected_grad_term": "2020A",
            "majors": [
                {
                    "major_name": "Wharton Ung Program - Undeclared",
                    "major_code": "WUNG"
                }
            ]
        }
    ],
    "courses": [
        {
            "term": "2019A",
            "name": "Advanced Corp Finance",
            "dept": "FNCE",
            "code": "203",
            "section": "001",
            "building": "JMHH",
            "room": "370",
            "weekdays": "MW",
            "start_date": "2019-01-16",
            "end_date": "2019-05-01",
            "start_time": "10:30 AM",
            "end_time": "12:00 PM",
            "instructors": [
                "Christian Opp",
                "Kevin Kaiser"
            ],
            "meeting_times": [
                {
                    "weekday": "M",
                    "start_time": "10:00 AM",
                    "end_time": "11:00 AM",
                    "building": "JMHH",
                    "room": "255"
                },
                {
                    "weekday": "W",
                    "start_time": "10:00 AM",
                    "end_time": "11:00 AM",
                    "building": "TOWN",
                    "room": "100"
                },
                {
                    "weekday": "R",
                    "start_time": "2:00 PM",
                    "end_time": "3:00 PM"
                }
            ]
        }
    ]
}
"""


@app.route('/account/register', methods=['POST'])
def register_account_endpoint():
    """ Add/update a Penn account in the database with degrees (optional) and current courses (optional) """
    json = request.get_json()
    if json:
        try:
            account = get_account(json)

            try:
                sqldb.session.add(account)
                sqldb.session.commit()
            except IntegrityError:
                sqldb.session.rollback()
                account = update_account(account)
                sqldb.session.commit()

            degrees = json.get("degrees")
            if degrees:
                add_schools_and_majors(account, degrees)

            courses = json.get("courses")
            if courses:
                add_courses(account, courses)

            return jsonify({'account_id': account.id})
        except KeyError as e:
            return jsonify({'error': str(e)}), 400
    else:
        return jsonify({'error': "JSON not passed"}), 400


@app.route('/account/courses', methods=['POST'])
def update_courses_endpoint():
    """ Add/Update the courses associated with the account """
    json = request.get_json()
    if json:
        try:
            account_id = json["account_id"]
            account = Account.query.filter_by(id=account_id).first()

            if account is None:
                return jsonify({'error': "Account not found."}), 400

            courses = json.get("courses")
            if courses:
                add_courses(account, courses)

            return jsonify({'success': True})
        except KeyError as e:
            return jsonify({'error': str(e)}), 400
    else:
        return jsonify({'error': "JSON not passed"}), 400


@app.route('/account/courses', methods=['GET'])
def get_courses_endpoint():
    """ Get the courses associated with the account """
    account_id = request.args.get("account_id")
    date = request.args.get("date")
    weekday = request.args.get("weekday")
    if account_id is None:
        return jsonify({'error': "Missing account_id field."}), 400

    account = Account.query.filter_by(id=account_id).first()
    if account is None:
        return jsonify({'error': "Account not found."}), 400

    courses = get_courses(account, date, weekday, weekday is None)
    return jsonify({'courses': courses})


def get_account(json):
    first = json.get("first")
    last = json.get("last")
    pennkey = json.get("pennkey")

    if first is None:
        raise KeyError("first is missing")
    if last is None:
        raise KeyError("last is missing")
    if pennkey is None:
        raise KeyError("pennkey is missing")

    email = json.get("email")
    image_url = json.get("image_url")
    if email is None:
        email = get_potential_email(json)

    return Account(first=first, last=last, pennkey=pennkey, email=email, image_url=image_url)


def update_account(updated_account):
    # Update an account (guaranteed to exist because pennkey already in database and pennkey unique)
    account = Account.query.filter_by(pennkey=updated_account.pennkey).first()
    if account:
        account.first = updated_account.first
        account.last = updated_account.last
        account.email = updated_account.email
        account.image_url = updated_account.image_url
    return account


def get_potential_email(json):
    pennkey = json.get("pennkey")
    degrees = json.get("degrees", None)
    if degrees is None:
        return None

    email = None
    if degrees:
        for degree in degrees:
            code = degree.get("school_code")
            if code:
                if "WH" in code:
                    return "{}@wharton.upenn.edu".format(pennkey)
                elif "SAS" in code:
                    email = "{}@sas.upenn.edu".format(pennkey)
                elif "EAS" in code:
                    email = "{}@sas.upenn.edu".format(pennkey)
                elif "NURS" in code:
                    email = "{}@nursing.upenn.edu".format(pennkey)
    return email


def add_schools_and_majors(account, json_array):
    # Remove degrees in DB and replace with new ones (if any)
    SchoolMajorAccount.query.filter_by(account_id=account.id).delete()

    account_schools = []
    for json in json_array:
        school_name = json.get("school_name")
        school_code = json.get("school_code")
        degree_name = json.get("degree_name")
        degree_code = json.get("degree_code")
        majors = json.get("majors")
        expected_grad = json.get("expected_grad_term")

        if school_name is None:
            raise KeyError("school_name is missing")
        if school_code is None:
            raise KeyError("school_code is missing")
        if degree_name is None:
            raise KeyError("degree_name is missing")
        if degree_code is None:
            raise KeyError("degree_code is missing")
        if majors is None:
            raise KeyError("majors is missing")
        if expected_grad is None:
            raise KeyError("expected_grad_term is missing")

        school = School.query.filter_by(name=school_name, code=school_code).first()
        if school is None:
            school = School(name=school_name, code=school_code)
            sqldb.session.add(school)
            sqldb.session.commit()

        degree = Degree.query.filter_by(code=degree_code).first()
        if degree is None:
            degree = Degree(name=degree_name, code=degree_code, school_id=school.id)
            sqldb.session.add(degree)
            sqldb.session.commit()

        if majors:
            for mJSON in majors:
                major_name = mJSON.get("major_name")
                major_code = mJSON.get("major_code")

                if major_name is None:
                    raise KeyError("major_name is missing")
                if major_code is None:
                    raise KeyError("major_code is missing")

                major = Major.query.filter_by(code=major_code).first()
                if major is None:
                    major = Major(name=major_name, code=major_code, degree_code=degree_code)
                    sqldb.session.add(major)
                    sqldb.session.commit()

                asm = SchoolMajorAccount(account_id=account.id, school_id=school.id, major=major.code, expected_grad=expected_grad)
                account_schools.append(asm)
        else:
            asm = SchoolMajorAccount(account_id=account.id, school_id=school.id, major=None, expected_grad=expected_grad)
            account_schools.append(asm)

    if account_schools:
        for asm in account_schools:
            sqldb.session.add(asm)
        sqldb.session.commit()


def add_courses(account, json_array):
    courses_in_db = []
    courses_not_in_db = []
    course_instructors = {}
    course_meetings_times = {}
    for json in json_array:
        term = json.get("term")
        name = json.get("name")
        dept = json.get("dept")
        code = json.get("code")
        section = json.get("section")
        building = json.get("building")
        room = json.get("room")
        weekdays = json.get("weekdays")
        start_date_str = json.get("start_date")
        end_date_str = json.get("end_date")
        start_time = json.get("start_time")
        end_time = json.get("end_time")
        instructors = json.get("instructors")
        meeting_times = json.get("meeting_times")

        try:
            meeting_times = ast.literal_eval(str(meeting_times))
        except ValueError:
            print(name)
            print(meeting_times)

        parameters = [term, name, dept, code, section, weekdays, start_date_str, end_date_str, start_time, end_time, instructors]
        if any(x is None for x in parameters):
            raise KeyError("Course parameter is missing")

        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')

        if (start_date is None) or (end_date is None):
            raise KeyError("Date is not a valid format.")

        course = Course.query.filter_by(dept=dept, code=code, section=section, term=term).first()
        if course:
            courses_in_db.append(course)
        if course is None:
            identifier = "{}{}{}{}".format(term, dept, code, section)
            course_instructors[identifier] = instructors
            course_meetings_times[identifier] = meeting_times
            course = Course(term=term, name=name, dept=dept, code=code, section=section, building=building, room=room,
                            weekdays=weekdays, start_date=start_date, end_date=end_date, start_time=start_time,
                            end_time=end_time)
            courses_not_in_db.append(course)

    if courses_not_in_db:
        for course in courses_not_in_db:
            sqldb.session.add(course)
        sqldb.session.commit()
        for course in courses_not_in_db:
            identifier = "{}{}{}{}".format(course.term, course.dept, course.code, course.section)
            instructors = course_instructors.get(identifier)
            if instructors:
                for instructor in instructors:
                    cp = CourseInstructor(course_id=course.id, name=instructor)
                    sqldb.session.add(cp)
            meeting_times = course_meetings_times.get(identifier)
            add_meeting_times(course, meeting_times)
        courses_in_db.extend(courses_not_in_db)

    if courses_in_db:
        terms = set([x.term for x in courses_in_db])
        for term in terms:
            # Delete all courses associated with this account for this term
            query = sqldb.session.query(CourseAccount, Course).join(Course) \
                .filter(CourseAccount.account_id == account.id) \
                .filter(Course.term == term)
            for ca, course in query:
                sqldb.session.delete(ca)

        for course in courses_in_db:
            ca = CourseAccount(account_id=account.id, course_id=course.id)
            sqldb.session.add(ca)
        sqldb.session.commit()


def add_meeting_times(course, meeting_times_json):
    if meeting_times_json:
        if type(meeting_times_json) is not list:
            raise KeyError("Meeting times json is not a list.")

        for json in meeting_times_json:
            if type(json) is not dict:
                raise KeyError("Meeting time json is not a dictionary.")

            building = json.get("building")
            room = json.get("room")
            weekday = json.get("weekday")
            start_time = json.get("start_time")
            end_time = json.get("end_time")

            parameters = [weekday, start_time, end_time]
            if any(x is None for x in parameters):
                raise KeyError("Meeting time parameter is missing")

            if course.start_time != start_time or course.end_time != end_time or weekday not in course.weekdays:
                # Add flag to indicate that you need to lookup meeting times in the CourseMeetingTime table
                course.extra_meetings_flag = True
                print(course.name)
                print(course.id)
                print(json)

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
                        "term": course.term,
                        "name": course.name,
                        "dept": course.dept,
                        "code": course.code,
                        "section": course.section,
                        "building": meeting.building,
                        "room": meeting.room,
                        "weekdays": meeting.weekday,
                        "start_date": course.start_date.strftime("%Y-%m-%d"),
                        "end_date": course.end_date.strftime("%Y-%m-%d"),
                        "start_time": meeting.start_time,
                        "end_time": meeting.end_time
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
        identifier = "{}{}{}{}".format(course.term, course.dept, course.code, course.section)
        instructor_arr = course_instructor_dict.get(identifier)
        if instructor_arr:
            instructor_arr.append(instructor.name)
        else:
            course_instructor_dict[identifier] = [instructor.name]

    meeting_times_dict = {}
    if include_extra_meeting_times:
        # Iterate through each course and add its extra meetings times to the class
        for course in courses:
            identifier = "{}{}{}{}".format(course.term, course.dept, course.code, course.section)
            meetings = CourseMeetingTime.query.filter_by(course_id=course.id)
            meetings_json_array = []
            for meeting in meetings:
                meetings_json_array.append({
                    "weekday": meeting.weekday,
                    "start_time": meeting.start_time,
                    "end_time": meeting.end_time,
                    "building": meeting.building,
                    "room": meeting.room
                })
            meeting_times_dict[identifier] = meetings_json_array

    for json in json_array:
        identifier = "{}{}{}{}".format(json["term"], json["dept"], json["code"], json["section"])
        json["instructors"] = course_instructor_dict.get(identifier)

    for course in courses:
        identifier = "{}{}{}{}".format(course.term, course.dept, course.code, course.section)
        json_array.append({
            "term": course.term,
            "name": course.name,
            "dept": course.dept,
            "code": course.code,
            "section": course.section,
            "building": course.building,
            "room": course.room,
            "weekdays": course.weekdays,
            "start_date": course.start_date.strftime("%Y-%m-%d"),
            "end_date": course.end_date.strftime("%Y-%m-%d"),
            "start_time": course.start_time,
            "end_time": course.end_time,
            "instructors": course_instructor_dict.get(identifier),
            "meeting_times": meeting_times_dict.get(identifier)
        })
    return json_array


def get_current_term_courses(account):
    now = datetime.datetime.now()
    now_str = now.strftime("%Y-%m-%d")
    return get_courses(account, now_str)


def get_todays_courses(account):
    return get_courses_in_N_days(account, 0)


def get_courses_in_N_days(account, inDays):
    now = datetime.datetime.now()
    today = now.strftime("%Y-%m-%d")
    weekday_array = ["S", "M", "T", "W", "R", "F", "S"]
    weekday = weekday_array[(int(now.strftime("%w")) + inDays) % 7]
    return get_courses(account, today, weekday)
