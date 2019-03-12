import requests
import datetime

from flask import jsonify, request

from server import app, db, sqldb
from .models import Account, School, Degree, Major, SchoolMajorAccount, Course, CourseAccount, CourseInstructor
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
			"code": "FNCE-203",
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
    if account_id is None:
    	return jsonify({'error': "Missing account_id field."}), 400

    account = Account.query.filter_by(id=account_id).first()
    if account is None:
    	return jsonify({'error': "Account not found."}), 400

    courses = get_courses(account)
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
			code = degree.get("division_code")
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
		if school is None:
			degree = Degree(name=school_name, code=school_code, school_id=school.id)
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
	for json in json_array:
		term = json.get("term")
		name = json.get("name")
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

		if (term is None) or (name is None) or (code is None) or (section is None) or (weekdays is None) \
			or (start_date_str is None) or (end_date_str is None) or (start_time is None) or (end_time is None) \
			or (instructors is None):
			raise KeyError("Course parameter is missing")

		start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
		end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')

		if (start_date is None) or (end_date is None):
			raise KeyError("Date is not a valid format.")

		course = Course.query.filter_by(code=code, section=section, term=term).first()
		if course:
			courses_in_db.append(course)
		if course is None:
			identifier = "{}{}{}".format(term, code, section)
			course_instructors[identifier] = instructors
			course = Course(term=term, name=name, code=code, section=section, building=building, room=room, 
				weekdays=weekdays, start_date=start_date, end_date=end_date, start_time=start_time, 
				end_time=end_time)
			courses_not_in_db.append(course)

	if courses_not_in_db:
		for course in courses_not_in_db:
			sqldb.session.add(course)
		sqldb.session.commit()
		for course in courses_not_in_db:
			identifier = "{}{}{}".format(course.term, course.code, course.section)
			instructors = course_instructors.get(identifier)
			if instructors:
				for instructor in instructors:
					cp = CourseInstructor(course_id=course.id, name=instructor)
					sqldb.session.add(cp)
		courses_in_db.extend(courses_not_in_db)

	if courses_in_db:
		terms = set([x.term for x in courses_in_db])
		for term in terms:
			# Delete all courses associated with this account for this term
			query = sqldb.session.query(CourseAccount, Course).join(Course) \
				.filter(CourseAccount.account_id==account.id) \
				.filter(Course.term==term)
			for ca, course in query:
				sqldb.session.delete(ca)

		for course in courses_in_db:
			ca = CourseAccount(account_id=account.id, course_id=course.id)
			sqldb.session.add(ca)
		sqldb.session.commit()


def get_courses(account, day=None, weekday=None):
	if day and weekday:
		course_query = sqldb.session.query(CourseAccount, Course).join(Course) \
		.filter(CourseAccount.account_id==account.id) \
		.filter(Course.end_date >= day) \
		.filter(Course.start_date <= day) \
		.filter(Course.weekdays.contains(weekday))
	elif day:
		course_query = sqldb.session.query(CourseAccount, Course).join(Course) \
		.filter(CourseAccount.account_id==account.id) \
		.filter(Course.end_date >= day) \
		.filter(Course.start_date <= day)
	else:
		course_query = sqldb.session.query(CourseAccount, Course).join(Course) \
		.filter(CourseAccount.account_id==account.id)

	courses = [course for (ca, course) in course_query]
	course_ids = [course.id for course in courses]
	instructor_query = sqldb.session.query(Course, CourseInstructor).join(CourseInstructor) \
		.filter(CourseInstructor.course_id.in_(course_ids))

	course_instructor_dict = {}
	for course, instructor in instructor_query:
		identifier = "{}{}{}".format(course.term, course.code, course.section)
		instructor_arr = course_instructor_dict.get(identifier)
		if instructor_arr:
			instructor_arr.append(instructor.name)
		else:
			course_instructor_dict[identifier] = [instructor.name]

	json = []
	for course in courses:
		identifier = "{}{}{}".format(course.term, course.code, course.section)
		json.append({
				"term": course.term,
				"name": course.name,
				"code": course.code,
				"section": course.section,
				"building": course.building,
				"room": course.room,
				"weekdays": course.weekdays,
				"start_date": course.start_date.strftime("%Y-%m-%d"),
				"end_date": course.end_date.strftime("%Y-%m-%d"),
				"start_time": course.start_time,
				"end_time": course.end_time,
				"instructors": course_instructor_dict.get(identifier)
			})

	return json


def get_current_term_courses(account):
	now = datetime.datetime.now()
	now_str= datetime.datetime.strftime("%Y-%m-%d")
	return get_courses(account, now_str)


def get_todays_courses(account):
	now = datetime.datetime.now()
	today= now.strftime("%Y-%m-%d")
	weekday_array = [None, "M", "T", "W", "R", "F", None]
	weekday = weekday_array[int(now.strftime("%w"))]
	return get_courses(account, today, weekday)
