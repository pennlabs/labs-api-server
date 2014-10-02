from flask import Flask, g, session, jsonify, Response, request, json, render_template, redirect, current_app, jsonify
from server import app, db
from werkzeug.security import generate_password_hash, check_password_hash
import json
import string
import datetime
from bson.objectid import ObjectId
import re
import requests
from penn import directory, dining, registrar

din = dining.Dining('UPENN_OD_emwd_1000807', '5h2g1ihbitu91uhgh3un9rliav')
reg = registrar.Registrar("UPENN_OD_emxL_1000903", "pt3sicp3q81tgul5qkbeg3rji5")
penn_dir = directory.Directory("UPENN_OD_emxM_1000904", "t4ii5rdud602n63ln2h1ld29hr")


# Dining API
@app.route('/dining/venues', methods=['GET'])
def retrieve_venues():
    venues = din.venues()
    return json.dumps(venues["result_data"])
    if (db.exists('dining:venues')):
        return db.get('dining:venues')
    else:
        venues = din.venues()
        db.set('dining:venues', json.dumps(venues["result_data"]))
        return jsonify(venues["result_data"])


@app.route('/dining/weekly_menu/<venue_id>', methods=['GET'])
def retrieve_weekly_menu(venue_id):
    venue_id = venue_id
    if (db.exists("dining:venues:weekly:%s" % (venue_id))):
        return db.get("dining:venues:weekly:%s" % (venue_id))
    else:
        menu = din.menu_weekly(venue_id)
        db.set('dining:venues:weekly:%s' % (venue_id), json.dumps(menu["result_data"]))
        return json.dumps(menu["result_data"])


@app.route('/dining/daily_menu/<venue_id>', methods=['GET'])
def retrieve_daily_menu(venue_id):
    venue_id = venue_id
    if (db.exists("dining:venues:daily:%s" % (venue_id))):
        return db.get("dining:venues:daily:%s" % (venue_id))
    else:
        menu = din.menu_daily(venue_id)
        db.set('dining:venues:daily:%s' % (venue_id), json.dumps(menu["result_data"]))
        return json.dumps(menu["result_data"])


# Directory API
@app.route('/directory/search', methods=['GET'])
def detail_search():
    if (len(request.args) > 0):
        data = penn_dir.detail_search(request.args)
        return json.dumps(data["result_data"])
    else:
        return jsonify({"error": "Please specify search parameters in the query string"})


@app.route('/directory/person/<person_id>', methods=['GET'])
def person_details(person_id):
    if (db.exists("directory:person:%s" % (person_id))):
        return db.get("directory:person:%s" % (person_id))
    else:
        data = penn_dir.person_details(person_id)
        db.set('directory:person:%s' % (person_id), json.dumps(data["result_data"]))
        return jsonify(data["result_data"])


def get_serializable_course(course):
    return {
        '_id': str(course.get('_id', '')),
        'dept': course.get('dept', ''),
        'title': course.get('title', ''),
        'courseNumber': course.get('courseNumber', ''),
        'credits': course.get('credits'),
        'sectionNumber': course.get('sectionNumber', ''),
        'type': course.get('type', ''),
        'times': course.get('times', ''),
        'days': course.get('days', ''),
        'hours': course.get('hours', ''),
        'building': course.get('building'),
        'roomNumber': course.get('roomNumber'),
        'prof': course.get('prof')
    }


def create_or_query(fields, regex):
    query = {'$or': []}
    for field in fields:
        query['$or'].append({field: regex})
    return query


def array_from_cursor(cursor, max_limit):
    return_arr = []
    for item in cursor:
        if len(return_arr) >= max_limit:
            break
        return_arr.append(get_serializable_course(item))
    return return_arr


def search_with_query(search_query):
    search_query_regex = {'$regex': search_query.replace(' ', '.*'), '$options': 'i'}

    registrar_search_query = create_or_query(['dept', 'title', 'sectionNumber', 'courseNumber'],
                                             search_query_regex)
    registrar_search_results = db.registrar.find(registrar_search_query).limit(50)
    courses = array_from_cursor(registrar_search_results, 50)

    return {
        'courses': courses
    }


def search_course(course):
    d = {key: value for key, value in course.iteritems()
         if value and key != 'gen_search'}
    courses = db.registrar.find(d)
    final_courses = array_from_cursor(courses, 50)
    return {"courses": final_courses}


def get_type_search(search_query):
    course = {'courseNumber': '',
              'sectionNumber': '',
              'dept': ''}
    search_punc = re.sub('[%s]' % re.escape(string.punctuation), '', search_query)
    split = re.split('(\d+)', search_punc)
    for s in split:
        s = s.strip()
        if s.isalpha() and (len(s) == 4 or len(s) == 3):
            course['dept'] = s
        elif s.isdigit():
            if (len(s) == 3):
                course['courseNumber'] = s
            if (len(s) == 6):
                course['courseNumber'] = s[:3]
                course['sectionNumber'] = s[-3:]
        else:
            course['gen_search'] = search_query
    return course


@app.route('/registrar/<search_query>', methods=['GET'])
def search(search_query):
    search_query = search_query.upper()
    query_results = search_course(get_type_search(search_query))
    if not query_results:
        query_results = search_with_query(search_query)
    return jsonify(query_results)
