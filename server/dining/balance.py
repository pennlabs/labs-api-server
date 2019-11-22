import datetime

import pandas as pd
from bs4 import BeautifulSoup
from flask import jsonify, request

from server import app
from server.models import Account, DiningBalance, sqldb
from server.penndata import wharton


@app.route('/dining/balance/v2', methods=['POST'])
def parse_and_save_dining_balance():
    try:
        account = Account.get_account()
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400

    html = request.form.get('html')
    if 'You are not currently signed up' in html:
        return jsonify({'hasPlan': False, 'balance': None, 'error': None})

    soup = BeautifulSoup(html, 'html.parser')
    divs = soup.findAll('div', {'class': 'info-column'})
    dollars = None
    swipes = None
    guest_swipes = None
    added_swipes = None
    if len(divs) >= 4:
        for div in divs[:4]:
            if 'Dining Dollars' in div.text:
                dollars = float(div.span.text[1:])
            elif 'Regular Visits' in div.text:
                swipes = int(div.span.text)
            elif 'Guest Visits' in div.text:
                guest_swipes = int(div.span.text)
            elif 'Add-on Visits' in div.text:
                added_swipes = int(div.span.text)
    else:
        return jsonify({'success': False, 'error': 'Something went wrong parsing HTML.'}), 400

    total_swipes = swipes + added_swipes
    dining_balance = DiningBalance(account_id=account.id, dining_dollars=dollars, swipes=total_swipes,
                                   guest_swipes=guest_swipes)
    sqldb.session.add(dining_balance)
    sqldb.session.commit()

    balance = {'dollars': dollars, 'swipes': total_swipes, 'guest_swipes': guest_swipes}
    return jsonify({'hasPlan': True, 'balance': balance, 'error': None})


@app.route('/dining/balance', methods=['POST'])
def save_dining_balance():
    try:
        account = Account.get_account()
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400

    dining_dollars_str = request.form.get('dining_dollars')
    swipes_str = request.form.get('swipes')
    guest_swipes_str = request.form.get('guest_swipes')

    if dining_dollars_str and swipes_str and guest_swipes_str:
        dollars = float(dining_dollars_str)
        swipes = int(swipes_str)
        g_swipes = int(guest_swipes_str)

        dining_balance = DiningBalance(account_id=account.id, dining_dollars=dollars, swipes=swipes,
                                       guest_swipes=g_swipes)
        sqldb.session.add(dining_balance)
        sqldb.session.commit()

        return jsonify({'success': True, 'error': None})
    else:
        return jsonify({'success': False, 'error': 'Field missing'}), 400


@app.route('/dining/balance', methods=['GET'])
def get_dining_balance():
    try:
        account = Account.get_account()
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400

    dining_balance = DiningBalance.query.filter_by(account_id=account.id) \
        .order_by(DiningBalance.created_at.desc()).first()

    if dining_balance:
        dining_dollars = dining_balance.dining_dollars
        swipes = dining_balance.swipes
        guest_swipes = dining_balance.guest_swipes
        created_at = dining_balance.created_at
        timestamp = created_at.strftime('%Y-%m-%dT%H:%M:%S') + '-{}'.format(wharton.get_dst_gmt_timezone())

        return jsonify({'balance': {
            'dining_dollars': dining_dollars,
            'swipes': swipes,
            'guest_swipes': guest_swipes,
            'timestamp': timestamp
        }})
    else:
        return jsonify({'balance': None})


@app.route('/dining/balances', methods=['GET'])
def get_average_balances_by_day():
    try:
        account = Account.get_account()
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400

    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    if start_date_str and end_date_str:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
        dining_balance = DiningBalance.query.filter_by(account_id=account.id) \
            .filter(DiningBalance.created_at >= start_date, DiningBalance.created_at <= end_date)
    else:
        dining_balance = DiningBalance.query.filter_by(account_id=account.id)

    balance_array = []
    if dining_balance:
        for balance in dining_balance:
            balance_array.append({
                'dining_dollars': balance.dining_dollars,
                'swipes': balance.swipes,
                'guest_swipes': balance.guest_swipes,
                'timestamp': balance.created_at.strftime('%Y-%m-%d')
            })

        df = pd.DataFrame(balance_array).groupby('timestamp').agg(lambda x: x.mean()).reset_index()
        return jsonify({'balance': df.to_dict('records')})

    return jsonify({'balance': None})


@app.route('/dining/projection', methods=['GET'])
def get_dining_projection():
    try:
        account = Account.get_account()
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400

    dining_balance = DiningBalance.query.filter_by(account_id=account.id)
    date = request.args.get('date')

    if date:
        date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
    else:
        today = datetime.date.today()
        month = int(today.strftime('%m'))
        if month <= 5:
            date = today.replace(month=5, day=5)
        elif month <= 8:
            date = today.replace(month=8, day=20)
        else:
            date = today.replace(month=12, day=15)

    balance_array = []
    if dining_balance:
        for balance in dining_balance:
            balance_array.append({
                'dining_dollars': balance.dining_dollars,
                'swipes': balance.swipes,
                'timestamp': balance.created_at.strftime('%Y-%m-%d')
            })

        df = pd.DataFrame(balance_array).groupby('timestamp').agg(lambda x: x.mean()).reset_index()

        if df.iloc[-1, 0] == 0.0 and df.iloc[-1, 1] == 0.0:
            return jsonify({
                'projection': {
                    'swipes_day_left': 0.0,
                    'dining_dollars_day_left': 0.0,
                    'swipes_left_on_date': 0.0,
                    'dollars_left_on_date': 0.0
                }
            })

        df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d')

        last_day_before_sem = df[(df['dining_dollars'] == 0) & (df['swipes'] == 0)]
        if last_day_before_sem.any().any():
            last_zero_timestamp = last_day_before_sem.tail(1).iloc[0]['timestamp']
            df = df[df['timestamp'] > last_zero_timestamp]

        if len(df.index) <= 5:
            return jsonify({'success': False, 'error': 'Insufficient previous transactions'}), 501

        num_days = abs((df.tail(1).iloc[0]['timestamp'] - df.head(1).iloc[0]['timestamp']).days) + 1
        num_swipes = df.head(1).iloc[0]['swipes'] - df.tail(1).iloc[0]['swipes']
        num_dollars = df.head(1).iloc[0]['dining_dollars'] - df.tail(1).iloc[0]['dining_dollars']
        swipes_per_day = num_swipes / num_days
        dollars_per_day = num_dollars / num_days

        swipe_days_left = df.tail(1).iloc[0]['swipes'] / swipes_per_day if num_swipes else 0.0
        dollars_days_left = df.tail(1).iloc[0]['dining_dollars'] / dollars_per_day if num_dollars else 0.0

        day_difference = abs((date - datetime.date.today()).days) + 1
        swipes_left = df.tail(1).iloc[0]['swipes'] - (swipes_per_day * day_difference) if num_swipes else 0.0
        dollars_left = df.tail(1).iloc[0]['dining_dollars'] - (dollars_per_day * day_difference) if num_dollars else 0.0

        if swipes_left <= 0:
            swipes_left = 0.0
        if dollars_left <= 0:
            dollars_left = 0.0

        return jsonify({
            'projection': {
                'swipes_day_left': swipe_days_left,
                'dining_dollars_day_left': dollars_days_left,
                'swipes_left_on_date': swipes_left,
                'dollars_left_on_date': dollars_left
            }
        })

    return jsonify({'projection': None})
