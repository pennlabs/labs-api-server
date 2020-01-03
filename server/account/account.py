from flask import jsonify, request
from sqlalchemy.exc import IntegrityError

from server import app, sqldb
from server.account.courses import add_courses
from server.account.degrees import add_schools_and_majors
from server.models import Account


"""
Example: JSON Encoding
{
    'first': 'Josh',
    'last': 'Doman',
    'image_url': null,
    'pennkey': 'joshdo',
    'pennid': '144363238',
    'degrees': [
        {
            'school_name': 'Engineering & Applied Science',
            'school_code': 'EAS',
            'degree_name':'Bachelor of Science in Economics',
            'degree_code':'BS',
            'expected_grad_term': '2020A',
            'majors': [
                {
                    'major_name': 'Applied Science - Computer Science',
                    'major_code': 'ASCS'
                }
            ]
        }, {
            'school_name': 'Wharton Undergraduate',
            'school_code': 'WH',
            'degree_name':'Bachelor of Applied Science',
            'degree_code':'BAS',
            'expected_grad_term': '2020A',
            'majors': [
                {
                    'major_name': 'Wharton Ung Program - Undeclared',
                    'major_code': 'WUNG'
                }
            ]
        }
    ],
    'courses': [
        {
            'term': '2019A',
            'name': 'Advanced Corp Finance',
            'dept': 'FNCE',
            'code': '203',
            'section': '001',
            'building': 'JMHH',
            'room': '370',
            'weekdays': 'MW',
            'start_date': '2019-01-16',
            'end_date': '2019-05-01',
            'start_time': '10:30 AM',
            'end_time': '12:00 PM',
            'instructors': [
                'Christian Opp',
                'Kevin Kaiser'
            ],
            'meeting_times': [
                {
                    'weekday': 'M',
                    'start_time': '10:00 AM',
                    'end_time': '11:00 AM',
                    'building': 'JMHH',
                    'room': '255'
                },
                {
                    'weekday': 'W',
                    'start_time': '10:00 AM',
                    'end_time': '11:00 AM',
                    'building': 'TOWN',
                    'room': '100'
                },
                {
                    'weekday': 'R',
                    'start_time': '2:00 PM',
                    'end_time': '3:00 PM'
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

            degrees = json.get('degrees')
            if degrees:
                add_schools_and_majors(account, degrees)

            courses = json.get('courses')
            if courses:
                add_courses(account, courses)

            return jsonify({'account_id': account.id})
        except KeyError as e:
            return jsonify({'error': str(e)}), 400
    else:
        return jsonify({'error': 'JSON not passed'}), 400


def get_account(json):
    first = json.get('first')
    last = json.get('last')
    pennkey = json.get('pennkey')

    if first is None:
        raise KeyError('first is missing')
    if last is None:
        raise KeyError('last is missing')
    if pennkey is None:
        raise KeyError('pennkey is missing')

    pennid = json.get('pennid')
    email = json.get('email')
    image_url = json.get('image_url')
    if email is None:
        email = get_potential_email(json)

    return Account(first=first, last=last, pennkey=pennkey, pennid=pennid, email=email, image_url=image_url)


def update_account(updated_account):
    # Update an account (guaranteed to exist because pennkey already in database and pennkey unique)
    account = Account.query.filter_by(pennkey=updated_account.pennkey).first()
    if account:
        account.first = updated_account.first
        account.last = updated_account.last
        if updated_account.email:
            account.email = updated_account.email
        if updated_account.image_url:
            account.image_url = updated_account.image_url
        if updated_account.pennid:
            account.pennid = updated_account.pennid
    return account


def get_potential_email(json):
    pennkey = json.get('pennkey')
    degrees = json.get('degrees', None)
    if degrees is None:
        return None

    email = None
    if degrees:
        for degree in degrees:
            code = degree.get('school_code')
            if code:
                if 'WH' in code:
                    return '{}@wharton.upenn.edu'.format(pennkey)
                elif 'COL' in code:
                    email = '{}@sas.upenn.edu'.format(pennkey)
                elif 'SAS' in code:
                    email = '{}@sas.upenn.edu'.format(pennkey)
                elif 'EAS' in code:
                    email = '{}@seas.upenn.edu'.format(pennkey)
                elif 'NUR' in code:
                    email = '{}@nursing.upenn.edu'.format(pennkey)
                elif 'SOD' in code:
                    email = '{}@design.upenn.edu'.format(pennkey)
                elif 'EDG' in code:
                    email = '{}@gse.upenn.edu'.format(pennkey)
                elif 'GEP' in code:
                    email = '{}@seas.upenn.edu'.format(pennkey)
                elif 'GAS' in code:
                    email = '{}@sas.upenn.edu'.format(pennkey)
                elif 'GEN' in code:
                    email = '{}@seas.upenn.edu'.format(pennkey)
                elif 'EDP' in code:
                    email = '{}@gse.upenn.edu'.format(pennkey)
                elif 'LPS' in code:
                    email = '{}@sas.upenn.edu'.format(pennkey)
                elif 'SP2' in code:
                    email = '{}@upenn.edu'.format(pennkey)
                elif 'NUG' in code:
                    email = '{}@nursing.upenn.edu'.format(pennkey)
    return email
