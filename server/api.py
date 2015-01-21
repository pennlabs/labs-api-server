from flask import Flask, g, session, jsonify, Response, request, json, render_template, redirect, current_app, jsonify
from server import app, db
from werkzeug.security import generate_password_hash, check_password_hash
import json
import string
import datetime
from bson.objectid import ObjectId
import re
import requests
from penndata import *

# Dining API
@app.route('/dining/venues', methods=['GET'])
def retrieve_venues():
    now = datetime.datetime.today()
    daysTillWeek = 6 - now.weekday()
    td = datetime.timedelta(days = daysTillWeek)
    month = now + td
    month.replace(hour=23, minute=59, second=59)
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
    endWeek = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=daysTillWeek);
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
    endDay = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1)
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

    if (db.exists("directory:search:%s" % (name))):
        return jsonify(json.loads(db.get("directory:search:%s" % (name))))

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
      param['affiliation'] = 'FAC'
    for param in params:
        data = penn_dir.search(param)
        for result in data['result_data']:
            person_id = result['person_id']
            if person_id not in ids:
                final.append(result)
                ids.add(person_id)

    now = datetime.datetime.today()
    td = datetime.timedelta(days = 30)
    month = now + td

    final = {'result_data':final}

    db.set('directory:search:%s' % (name), json.dumps(final))
    db.pexpireat('directory:search:%s' % (name), month)
    return jsonify(final)


@app.route('/directory/person/<person_id>', methods=['GET'])
def person_details(person_id):
    now = datetime.datetime.today()
    td = datetime.timedelta(days = 30)
    month = now + td
    if (db.exists("directory:person:%s" % (person_id))):
        return jsonify(json.loads(db.get("directory:person:%s" % (person_id))))
    else:
        data = penn_dir.person_details(person_id)
        db.set('directory:person:%s' % (person_id), json.dumps(data["result_data"][0]))
        db.pexpireat('directory:person:%s' % (person_id), month)
        return jsonify(data["result_data"][0])

def is_dept(keyword):
    depts = {
      "AAMW" : "Art & Arch of Med. World",
      "ACCT" : "Accounting",
      "AFRC" : "Africana Studies",
      "AFST" : "African Studies Program",
      "ALAN" : "Asian Languages",
      "AMCS" : "Applied Math & Computatnl Sci.",
      "ANAT" : "Anatomy",
      "ANCH" : "Ancient History",
      "ANEL" : "Ancient Near East Languages",
      "ANTH" : "Anthropology",
      "ARAB" : "Arabic",
      "ARCH" : "Architecture",
      "ARTH" : "Art History",
      "ASAM" : "Asian American Studies",
      "ASTR" : "Astronomy",
      "BCHE" : "Biochemistry (Undergrads)",
      "BE" : "Bioengineering",
      "BENG" : "Bengali",
      "BEPP" : "Business Econ & Public Policy",
      "BFMD" : "Benjamin Franklin Seminars-Med",
      "BIBB" : "Biological Basis of Behavior",
      "BIOE" : "Bioethics",
      "BIOL" : "Biology",
      "BIOM" : "Biomedical Studies",
      "BMB" : "Biochemistry & Molecular Biophy",
      "BSTA" : "Biostatistics",
      "CAMB" : "Cell and Molecular Biology",
      "CBE" : "Chemical & Biomolecular Engr",
      "CHEM" : "Chemistry",
      "CHIN" : "Chinese",
      "CINE" : "Cinema Studies",
      "CIS" : "Computer and Information Sci",
      "CIT" : "Computer and Information Tech",
      "CLST" : "Classical Studies",
      "COGS" : "Cognitive Science",
      "COLL" : "College",
      "COML" : "Comparative Literature",
      "COMM" : "Communications",
      "CPLN" : "City Planning",
      "CRIM" : "Criminology",
      "DEMG" : "Demography",
      "DORT" : "Orthodontics",
      "DOSP" : "Oral Surgery and Pharmacology",
      "DPED" : "Pediatric Dentistry",
      "DRST" : "Restorative Dentistry",
      "DTCH" : "Dutch",
      "DYNM" : "Organizational Dynamics",
      "EALC" : "East Asian Languages & Civilztn",
      "EAS" : "Engineering & Applied Science",
      "ECON" : "Economics",
      "EDUC" : "Education",
      "EEUR" : "East European",
      "ENGL" : "English",
      "ENGR" : "Engineering",
      "ENM" : "Engineering Mathematics",
      "ENVS" : "Environmental Studies",
      "EPID" : "Epidemiology",
      "ESE" : "Electric & Systems Engineering",
      "FNAR" : "Fine Arts",
      "FNCE" : "Finance",
      "FOLK" : "Folklore",
      "FREN" : "French",
      "FRSM" : "Non-Sas Freshman Seminar",
      "GAFL" : "Government Administration",
      "GAS" : "Graduate Arts & Sciences",
      "GCB" : "Genomics & Comp. Biology",
      "GEOL" : "Geology",
      "GREK" : "Greek",
      "GRMN" : "Germanic Languages",
      "GSWS" : "Gender,Sexuality & Women's Stud",
      "GUJR" : "Gujarati",
      "HCMG" : "Health Care Management",
      "HEBR" : "Hebrew",
      "HIND" : "Hindi",
      "HIST" : "History",
      "HPR" : "Health Policy Research",
      "HSOC" : "Health & Societies",
      "HSPV" : "Historic Preservation",
      "HSSC" : "History & Sociology of Science",
      "IMUN" : "Immunology",
      "INTG" : "Integrated Studies",
      "INTL" : "International Programs",
      "INTR" : "International Relations",
      "IPD" : "Integrated Product Design",
      "ITAL" : "Italian",
      "JPAN" : "Japanese",
      "JWST" : "Jewish Studies Program",
      "KORN" : "Korean",
      "LALS" : "Latin American & Latino Studies",
      "LARP" : "Landscape Arch & Regional Plan",
      "LATN" : "Latin",
      "LAW" : "Law",
      "LGIC" : "Logic, Information and Comp.",
      "LGST" : "Legal Studies & Business Ethics",
      "LING" : "Linguistics",
      "LSMP" : "Life Sciences Management Prog",
      "MAPP" : "Master of Applied Positive Psyc",
      "MATH" : "Mathematics",
      "MEAM" : "Mech Engr and Applied Mech",
      "MED" : "Medical",
      "MGEC" : "Management of Economics",
      "MGMT" : "Management",
      "MKTG" : "Marketing",
      "MLA" : "Master of Liberal Arts Program",
      "MLYM" : "Malayalam",
      "MMP" : "Master of Medical Physics",
      "MSCI" : "Military Science",
      "MSE" : "Materials Science and Engineer",
      "MSSP" : "Social Policy",
      "MTR" : "Mstr Sci Transltl Research",
      "MUSA" : "Master of Urban Spatial Analyt",
      "MUSC" : "Music",
      "NANO" : "Nanotechnology",
      "NELC" : "Near Eastern Languages & Civlzt",
      "NETS" : "Networked and Social Systems",
      "NGG" : "Neuroscience",
      "NPLD" : "Nonprofit Leadership",
      "NSCI" : "Naval Science",
      "NURS" : "Nursing",
      "OPIM" : "Operations and Information Mgmt",
      "PERS" : "Persian",
      "PHIL" : "Philosophy",
      "PHRM" : "Pharmacology",
      "PHYS" : "Physics",
      "PPE" : "Philosophy, Politics, Economics",
      "PRTG" : "Portuguese",
      "PSCI" : "Political Science",
      "PSYC" : "Psychology",
      "PUBH" : "Public Health Studies",
      "PUNJ" : "Punjabi",
      "REAL" : "Real Estate",
      "RELS" : "Religious Studies",
      "ROML" : "Romance Languages",
      "RUSS" : "Russian",
      "SAST" : "South Asia Studies",
      "SCND" : "Scandinavian",
      "SKRT" : "Sanskrit",
      "SLAV" : "Slavic",
      "SOCI" : "Sociology",
      "SPAN" : "Spanish",
      "STAT" : "Statistics",
      "STSC" : "Science, Technology & Society",
      "SWRK" : "Social Work",
      "TAML" : "Tamil",
      "TCOM" : "Telecommunications & Networking",
      "TELU" : "Telugu",
      "THAR" : "Theatre Arts",
      "TURK" : "Turkish",
      "URBS" : "Urban Studies",
      "URDU" : "Urdu",
      "VCSN" : "Clinical Studies - Nbc Elect",
      "VCSP" : "Clinical Studies - Phila Elect",
      "VIPR" : "Viper",
      "VISR" : "Vet School Ind Study & Research",
      "VLST" : "Visual Studies",
      "VMED" : "Csp/Csn Medicine Courses",
      "WH" : "Wharton Undergraduate",
      "WHCP" : "Wharton Communication Pgm",
      "WHG" : "Wharton Graduate",
      "WRIT" : "Writing Program",
      "YDSH" : "Yiddish"
    }
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
    return {"courses" : list(final_courses)}

def get_type_search(search_query):
    course = {'courseNumber': '',
              'sectionNumber': '',
              'dept': '',
              'desc_search': ''}
    search_punc = re.sub('[%s]' % re.escape(string.punctuation), ' ', search_query)
    def repl(matchobj):
        return matchobj.group(0)[0] + " " + matchobj.group(0)[1]
    search_presplit = re.sub('(\d[a-zA-z]|[a-zA-z]\d)', repl, search_punc)
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
    now = datetime.datetime.today()
    endDay = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1)
    if (db.exists('registrar_query:%s' % search_query)):
        return jsonify(json.loads(db.get('registrar_query:%s' % search_query)))
    else:
        query_results = search_course(get_type_search(search_query))
    if query_results is None:
        return jsonify({"Error": "The search query could not be processed"})
    db.set('registrar_query:%s' % search_query,  json.dumps(query_results))
    db.pexpireat('registrar_query:%s' % search_query, endDay)
    return jsonify(query_results)

@app.route('/buildings/<building_code>', methods=['GET'])
def building(building_code):
    if db.exists("buildings:%s" % (building_code)):
        building_info = db.get("buildings:%s" % (building_code))
        return jsonify(json.loads(building_info))
    else:
        return None

