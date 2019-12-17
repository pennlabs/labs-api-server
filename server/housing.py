from flask import jsonify, request
from server import app, auth
from bs4 import BeautifulSoup
import math
import requests
from server.models import Account


@app.route('/housing', methods=['POST'])
@auth()
def save_housing_info(account):
    print(account)

    html = request.form.get('html')

    soup = BeautifulSoup(html, 'html.parser')
    main = soup.findAll('div', {'class': 'interior-main-content col-md-6 col-md-push-3 md:mb-150'})[0]

    year_text = None
    house_text = None
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
    start_year, end_year = split[len(split) - 3], split[len(split) - 1]

    split = house_text.split("-")
    house = split[1].strip()

    split = room.text.split("  ")
    location = split[0].strip()

    split = address.text.split("  ")
    address = split[0].strip()

    print(start_year, end_year)
    print(house)
    print(location)
    print(address)

    return jsonify({ 'result': True })


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
