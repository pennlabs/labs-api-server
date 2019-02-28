import requests

from flask import jsonify, request

from server import app, db, sqldb
from .models import Account, School, Major, SchoolMajorAccount, Course, CourseAccount, CourseProfessor


"""
POST JSON Encoding
{
	"first": "Josh",
	"last": "Doman",
	"image_url": null,
	"pennkey": "joshdo",
	"degrees": [
		{
			"school_name": "Engineering & Applied Science",
			"school_code": "EAS",
			"majors": [
				{
					"major_name": "Applied Science - Computer Science",
					"major_code": "ASCS"
				}
			]
		}, {
			"school_name": "Wharton Undergraduate",
			"school_code": "WH",
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
			"building_code": 81,
			"weekdays": "MW",
			"start": "10:30 AM",
			"end": "12:00PM",
			"professors": [
				"Christian Opp",
				"Kevin Kaiser"
			]
		}
	]
}
"""


@app.route('/account/register', methods=['POST'])
def register_account():
    """ Temporary endpoint to allow non-authenticated users to access the list of GSRs. """
    json = request.get_json()
    if json:
    	try:
    		account = get_account(json)

    		sqldb.session.add(account)
    		sqldb.session.commit()

    		degrees = json.get("degrees")
    		if degrees:
    			add_schools_and_majors(account, degrees)

    		courses = json.get("courses")
    		if courses:
    			add_courses(account, courses)

    		return jsonify({'result': "success"})
    	except KeyError as e:
    		return jsonify({'error': str(e)}), 400
    else:
    	return jsonify({'error': "JSON not passed"}), 400


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
	account_schools = []
	for json in json_array:
		school_name = json.get("school_name")
		school_code = json.get("school_code")
		majors = json.get("majors")

		if school_name is None:
			raise KeyError("school_name is missing")
		if school_code is None:
			raise KeyError("school_code is missing")
		if majors is None:
			raise KeyError("majors is missing")

		school = School.query.filter_by(name=school_name, code=school_code).first()
		if school is None:
			school = School(name=school_name, code=school_code)
			sqldb.session.add(school)
			sqldb.session.commit()

		if majors:
			for mJSON in majors:
				major_name = mJSON.get("major_name")
				major_code = mJSON.get("major_code")

				if major_name is None:
					raise KeyError("major_name is missing")
				if major_code is None:
					raise KeyError("major_code is missing")

				major = Major.query.filter_by(name=major_name, code=major_code).first()
				if major is None:
					major = Major(name=major_name, code=major_code, school_code=school_code)
					sqldb.session.add(major)
					sqldb.session.commit()

				asm = SchoolMajorAccount(account_id=account.id, school_id=school.id, major=major.code)
				account_schools.append(asm)
		else:
			asm = SchoolMajorAccount(account_id=account.id, school_id=school.id, major=None)
			account_schools.append(asm)

	if account_schools:
		for asm in account_schools:
			sqldb.session.add(asm)
		sqldb.session.commit()


def add_courses(account, json_array):
	courses_in_db = []
	courses_not_in_db = []
	course_professors = {}
	for json in json_array:
		term = json.get("term")
		name = json.get("name")
		code = json.get("code")
		section = json.get("section")
		building = json.get("building")
		room = json.get("room")
		weekdays = json.get("weekdays")
		start = json.get("start")
		end = json.get("end")
		building_code_str = json.get("building_code")
		professors = json.get("professors")

		if (term is None) or (name is None) or (code is None) or (section is None) or (weekdays is None) \
			or (start is None) or (end is None) or (professors is None):
			raise KeyError("Course parameter is missing")

		try:
			building_code = int(building_code_str)
		except ValueError:
			raise KeyError("Building code is not an int.")

		course = Course.query.filter_by(code=code, section=section, term=term).first()
		if course:
			courses_in_db.append(course)
		if course is None:
			identifier = "{}{}{}".format(term, code, section)
			course_professors[identifier] = professors
			course = Course(term=term, name=name, code=code, section=section, building=building, room=room, 
				weekdays=weekdays, start=start, end=end, building_code=building_code)
			courses_not_in_db.append(course)

	if courses_not_in_db:
		for course in courses_not_in_db:
			sqldb.session.add(course)
		sqldb.session.commit()
		for course in courses_not_in_db:
			identifier = "{}{}{}".format(course.term, course.code, course.section)
			professors = course_professors.get(identifier)
			if professors:
				add_professors(course.id, professors)
		courses_in_db.extend(courses_not_in_db)

	if courses_in_db:
		for course in courses_in_db:
			ca = CourseAccount(account_id=account.id, course_id=course.id)
			sqldb.session.add(ca)
		sqldb.session.commit()


def add_professors(course_id, professors):
	for professor in professors:
		cp = CourseProfessor(course_id=course_id, name=professor)
		sqldb.session.add(cp)
	sqldb.session.commit()
