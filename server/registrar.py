from flask import request
from server import app
import string
import datetime
import re
from .base import cached_route
from .penndata import depts, reg


def is_dept(keyword):
    return keyword.upper() in depts.keys()


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
    params = dict()
    if len(course.get('dept', '')) > 0:
        id_param = ""
        id_param += course.get('dept').lower()
        if len(course.get('courseNumber', '')) > 0:
            id_param += "-" + course.get('courseNumber').lower()
            if len(course.get('sectionNumber', '')) > 0:
                id_param += course.get('sectionNumber').lower()
        params['course_id'] = id_param

    if len(course['desc_search']) > 0:
        params['description'] = course['desc_search']

    if len(params) == 0:
        return None
    final_courses = reg.search(params)
    return {"courses": list(final_courses)}


def get_type_search(search_query):
    course = {
        'courseNumber': '',
        'sectionNumber': '',
        'dept': '',
        'desc_search': ''
    }
    search_punc = re.sub('[%s]' % re.escape(string.punctuation), ' ',
                         search_query)

    def repl(matchobj):
        return matchobj.group(0)[0] + " " + matchobj.group(0)[1]

    search_presplit = re.sub('(\\d[a-zA-z]|[a-zA-z]\\d)', repl, search_punc)
    split = search_presplit.split()
    found_desc = False
    in_desc = False
    for s in split:
        s = s.strip()
        if s.isalpha() and is_dept(s.upper()):
            in_desc = False
            course['dept'] = s.upper()
        elif s.isdigit():
            in_desc = False
            if (len(s) == 3):
                course['courseNumber'] = s
            if (len(s) == 6):
                course['courseNumber'] = s[:3]
                course['sectionNumber'] = s[-3:]
        else:
            if not found_desc or in_desc:
                found_desc = True
                in_desc = True
                if len(course['desc_search']) == 0:
                    course['desc_search'] = s
                else:
                    course['desc_search'] += " " + s
    return course


@app.route('/registrar/search', methods=['GET'])
def search():
    search_query = request.args['q']

    def get_data():
        query_results = search_course(get_type_search(search_query))
        if query_results is None:
            return {"error": "The search query could not be processed."}
        else:
            return query_results

    return cached_route('registrar_query:%s' % search_query, datetime.timedelta(days=1),
                        get_data)


@app.route('/registrar/search/instructor', methods=['GET'])
def search_instructor():
    query = request.args['q']

    def get_data():
        results = reg.search({
            'instructor': query
        })
        if results is None:
            return {"error": "The search query could not be processed."}
        else:
            return {"courses": list(results)}

    return cached_route('registrar_query_instructor:%s' % query, datetime.timedelta(days=1), get_data)
