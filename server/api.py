from flask import Flask, g, session, jsonify, Response, request, json, render_template, redirect, current_app
from server import app, db
from werkzeug.security import generate_password_hash, check_password_hash
import json
import string
import datetime
from bson.objectid import ObjectId
import re
import requests

#general
def make_api_request(url, bearer, token):
    headers = {
        'Authorization-Bearer': bearer,
        'Authorization-Token': token,
        'Content-Type': 'application/json; charset=utf-8'}
    r = requests.get(url, headers=headers)
    print r.json()
    return r.json()

#Dining API
@app.route('/v1/dining/venues', methods=['GET'])
def retrieve_venues():
    if (db.exists('dining:venues')):
        return db.get('dining:venues')
    else:
        venues = make_api_request('https://esb.isc-seo.upenn.edu/8091/open_data/dining/venues',
                                  'UPENN_OD_emwd_1000807', '5h2g1ihbitu91uhgh3un9rliav')
        db.set('dining:venues', json.dumps(venues["result_data"]))
        return json.dumps(venues["result_data"])

@app.route('/v1/dining/venues/<venue_id>')
def retrieve_menu(venue_id):
    venue_id = venue_id
    if (db.exists("dining:venues:%s" % (venue_id))):
        return db.get("dining:venues:%s" % (venue_id))
    else:
        venue = make_api_request("https://esb.isc-seo.upenn.edu/8091/open_data/dining/menus/weekly/%s" % (venue_id),
                                   'UPENN_OD_emwd_1000807', '5h2g1ihbitu91uhgh3un9rliav')
        db.set('dining:venues:%s' % (venue_id), json.dumps(venue["result_data"]))
        return json.dumps(venue["result_data"])


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
    search_query_regex = { '$regex': search_query.replace(' ', '.*'), '$options': 'i'}

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
    return {"courses" : final_courses}

def get_type_search(search_query):
    course = {'courseNumber':'',
              'sectionNumber':'',
              'dept':''}
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


@app.route('/v1/registrar/<search_query>', methods=['GET'])
def search(search_query):
    search_query = search_query.upper()
    query_results = search_course(get_type_search(search_query))
    if not query_results:
        query_results = search_with_query(search_query)
    return jsonify(query_results)
