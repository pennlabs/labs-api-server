from flask import jsonify, request
import math
import requests
from datetime import datetime
from server import app, auth, sqldb
from bs4 import BeautifulSoup
from server.models import Account
from sqlalchemy.exc import IntegrityError


class Housing(sqldb.Model):
    account = sqldb.Column(sqldb.VARCHAR(255), sqldb.ForeignKey('account.id'), primary_key=True)
    house = sqldb.Column(sqldb.Text, nullable=True)
    location = sqldb.Column(sqldb.Text, nullable=True)
    address = sqldb.Column(sqldb.Text, nullable=True)
    off_campus = sqldb.Column(sqldb.Boolean, nullable=True)
    start = sqldb.Column(sqldb.Integer, primary_key=True, default=-1)
    end = sqldb.Column(sqldb.Integer, default=-1)
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())
    html = sqldb.Column(sqldb.Text, nullable=True)


@app.route('/housing', methods=['POST'])
@auth()
def save_housing_info(account):
    html = request.form.get('html')

    soup = BeautifulSoup(html, 'html.parser')
    html = soup.prettify().strip().strip('\t\r\n')

    housing = None
    try:
        house, location, address = None, None, None
        main = soup.findAll('div', {'class': 'interior-main-content col-md-6 col-md-push-3 md:mb-150'})[0]

        off_campus = 'You don\'t have any assignments at this time' in html
        if off_campus:
            # Off campus for 2020 - 2021 school year if today is after January and user has no assignments
            today = datetime.today()
            start = today.year if today.month > 1 else today.year - 1
            end = start + 1
        else:
            year_text, house_text = None, None
            headers = main.findAll('h3')
            for h3 in headers:
                if 'Academic Year' in h3.text:
                    year_text = h3.text
                elif 'House Information' in h3.text:
                    house_text = h3.text

            info = main.findAll('div', {'class': 'col-md-8'})[0]
            paragraphs = info.findAll('p')
            room = paragraphs[0]
            address = paragraphs[1]

            split = year_text.strip().split(" ")
            start, end = split[len(split) - 3], split[len(split) - 1]

            split = house_text.split("-")
            house = split[1].strip()

            split = room.text.split("  ")
            location = split[0].strip()

            split = address.text.split("  ")
            address = split[0].strip()

        housing = Housing(account=account.id, house=house, location=location, address=address, off_campus=off_campus, 
                            start=start, end=end, html=html)
    except (IndexError, AttributeError):
        # Parsing failed. Save the html so that we can diagnose the problem and update the account's info later.
        housing = Housing(account=account.id, html=html)

    try:
        sqldb.session.add(housing)
        sqldb.session.commit()
    except IntegrityError:
        sqldb.session.rollback()
        current_result = Housing.query.filter_by(account=account.id, start=housing.start).first()
        if current_result:
            if housing.off_campus or (housing.house and housing.location and housing.address):
                current_result.house = house
                current_result.location = location
                current_result.address = address
                current_result.off_campus = off_campus
            current_result.html = html
            sqldb.session.commit()

    if housing.start:
        return jsonify({
            'house': housing.house,
            'room': housing.location,
            'address': housing.address,
            'start': housing.start,
            'end': housing.end,
            'off_campus': housing.off_campus,
        })
    else:
        return jsonify({'error': 'Unable to parse HTML.'}), 400


@app.route('/housing', methods=['GET'])
@auth()
def get_housing_info(account):
    today = datetime.today()
    year = today.year if today.month > 5 else today.year - 1
    housing = Housing.query.filter_by(account=account.id, start=year).first()
    if housing:
        return jsonify({
            'result': {
                'house': housing.house,
                'room': housing.location,
                'address': housing.address,
                'start': housing.start,
                'end': housing.end,
                'off_campus': housing.off_campus,
            }
        })
    else:
        return jsonify({'result': None})


def get_details_for_location(location):
    """
    Ex: 403 Butcher (Bed space: a)
    Returns 403, 4, Butcher
    """
    split = location.split(" ")
    room = int(split[0].strip())
    floor = math.floor(room / 100)
    section = split[1].strip()

    return room, floor, section
