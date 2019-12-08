from flask import jsonify, request
from penn.base import APIError
from sqlalchemy import or_

from server import app
from server.models import Account


@app.route('/studyspaces/user/search', methods=['GET'])
def get_nam():
    """
    Gets users that match search query
    """

    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Query argument not found.'}), 400

    if len(query) <= 1:
    	return jsonify({'error': 'Query is too short. Minimum length is two characters.'}), 400

    # query = query.lower()
    starting_query = '{}%'.format(query)
    general_query = '%{}%'.format(query)

    starting_first_name_matches = Account.query.filter(Account.first.like(starting_query)).all()
    starting_last_name_matches = Account.query.filter(Account.last.like(starting_query)).all()
    general_first_name_matches = Account.query.filter(Account.first.like(general_query)).all()
    general_last_name_matches = Account.query.filter(Account.last.like(general_query)).all()

    users = starting_first_name_matches
    users.extend(starting_last_name_matches)
    users.extend(general_first_name_matches)
    users.extend(general_last_name_matches)

    seen_pennkeys = set()
    filtered_users = []
    for user in users:
    	if user.pennkey not in seen_pennkeys:
    		filtered_users.append(user)
    		seen_pennkeys.add(user.pennkey)

    filtered_users = [
    	{
    		'first': x.first,
    		'last': x.last,
    		'pennkey': x.pennkey,
    		'email': x.email,
    	} for x in filtered_users
    ]

    return jsonify({'results': filtered_users})
