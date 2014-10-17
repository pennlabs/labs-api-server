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
    now = datetime.datetime.today()
    td = datetime.timedelta(days = 30)
    month = now + td
    if (db.exists('dining:venues')):
        return jsonify(json.loads(db.get('dining:venues')))
    else:
        venues = din.venues()
        db.set('dining:venues', json.dumps(venues["result_data"]))
        db.pexpireat('dining:venues', month)
        return jsonify(venues["result_data"])


@app.route('/dining/weekly_menu/<venue_id>', methods=['GET'])
def retrieve_weekly_menu(venue_id):
    now = datetime.datetime.today()
    daysTillWeek = 6 - now.weekday()
    endWeek = datetime.datetime(now.year, now.month, now.day + daysTillWeek)
    venue_id = venue_id
    if (db.exists("dining:venues:weekly:%s" % (venue_id))):
        return jsonify(json.loads(db.get("dining:venues:weekly:%s" % (venue_id))))
    else:
        menu = din.menu_weekly(venue_id)
        db.set('dining:venues:weekly:%s' % (venue_id), json.dumps(menu["result_data"]))
        db.pexpireat('dining:venues:weekly:%s' % (venue_id), endWeek)
        return jsonify(menu["result_data"])


@app.route('/dining/daily_menu/<venue_id>', methods=['GET'])
def retrieve_daily_menu(venue_id):
    now = datetime.datetime.today()
    endDay = datetime.datetime(now.year, now.month, now.day + 1)
    venue_id = venue_id
    if (db.exists("dining:venues:daily:%s" % (venue_id))):
        return jsonify(json.loads(db.get("dining:venues:daily:%s" % (venue_id))))
    else:
        menu = din.menu_daily(venue_id)
        db.set('dining:venues:daily:%s' % (venue_id), json.dumps(menu["result_data"]))
        db.pexpireat('dining:venues:daily:%s' % (venue_id), endDay)
        return jsonify(menu["result_data"])


# Directory API
@app.route('/directory/search', methods=['GET'])
def detail_search():
    if not request.args.has_key('name'):
        return jsonify({"error": "Please specify search parameters in the query string"})

    name = request.args['name']
    arr = name.split()
    params = []


    if len(arr) > 1:

        if arr[0][-1] == ',':
            params = [{'last_name':arr[0][:-1], 'first_name':arr[1]}]
        else:
            params = [
                {'last_name':arr[-1], 'first_name':arr[0]},
                {'last_name':arr[0], 'first_name':arr[-1]}
            ]

    else:
        params = [{'last_name':name},{'first_name':name}]

    ids = set()
    final = []
    for param in params:
        data = penn_dir.detail_search(param)
        for result in data['result_data']:
            person_id = result['result_data'][0]['person_id']
            if person_id not in ids:
                final.append(result)
                ids.add(person_id)


    return jsonify({'result_data':final})


@app.route('/directory/person/<person_id>', methods=['GET'])
def person_details(person_id):
    now = datetime.datetime.today()
    td = datetime.timedelta(days = 30)
    month = now + td
    if (db.exists("directory:person:%s" % (person_id))):
        return db.get("directory:person:%s" % (person_id))
    else:
        data = penn_dir.person_details(person_id)
        db.set('directory:person:%s' % (person_id), json.dumps(data["result_data"]))
        db.pexpireat('directory:person:%s' % (person_id), month)
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

def search_course(course):
    d = {key: value for key, value in course.iteritems()
         if value and key != 'gen_search'}
    id_param = ""
    if len(course.get('dept', '')) > 0:
        id_param += course.get('dept').lower()
        if len(course.get('courseNumber', '')) > 0:
            id_param += "-" + course.get('courseNumber').lower()
            if len(course.get('sectionNumber', '')) > 0:
                id_param += course.get('sectionNumber').lower()
    else:
        return {"error": "Please include a department in your search."}

    final_courses = reg.search({'course_id': id_param})
    return {"courses" : list(final_courses)}

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


@app.route('/registrar/search', methods=['GET'])
def search():
    search_query = request.args['q']
    now = datetime.datetime.today()
    endDay = datetime.datetime(now.year, now.month, now.day + 1)
    search_query = search_query.upper()
    if (db.exists('registrar_query:%s' % search_query)):
        return jsonify(json.loads(db.get('registrar_query:%s' % search_query)))
    else:
        query_results = search_course(get_type_search(search_query))
        db.set('registrar_query:%s' % search_query,  json.dumps(query_results))
        db.pexpireat('registrar_query:%s' % search_query, endDay)
        return jsonify(query_results)
