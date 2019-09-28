import csv
import datetime

from flask import jsonify, request

from server import app, sqldb
from server.models import Account, DiningTransaction


@app.route('/dining/transactions', methods=['POST'])
def save_dining_dollar_transactions():
    try:
        account = Account.get_account()
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400

    last_transaction = sqldb.session.query(DiningTransaction.date) \
                                    .filter_by(account_id=account.id) \
                                    .order_by(DiningTransaction.date.desc()) \
                                    .first()

    decoded_content = request.form.get('transactions')
    cr = csv.reader(decoded_content.splitlines(), delimiter=',')

    # Create list of rows, remove headers, and reverse so in order of date
    row_list = list(cr)
    row_list.pop(0)
    row_list.reverse()

    for row in row_list:
        if len(row) == 4:
            if row[0] == 'No transaction history found for this date range.':
                continue
            else:
                date = datetime.datetime.strptime(row[0], '%m/%d/%Y %I:%M%p')
                if last_transaction is None or date > last_transaction.date:
                    transaction = DiningTransaction(account_id=account.id, date=date, description=row[1],
                                                    amount=float(row[2]), balance=float(row[3]))
                    sqldb.session.add(transaction)
    sqldb.session.commit()

    return jsonify({'success': True, 'error': None})
