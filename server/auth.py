from functools import wraps

import requests
from flask import jsonify, request

from server.models import Account


def auth():
    def _auth(f):
        @wraps(f)
        def __auth(*args, **kwargs):
            authorization = request.headers.get('Authorization')
            if authorization and ' ' in authorization:
                auth_type, token = authorization.split()
                if auth_type == 'Bearer':  # Only validate if Authorization header type is Bearer
                    try:
                        body = {'token': token}
                        headers = {'Authorization': 'Bearer {}'.format(token)}
                        data = requests.post(
                            url='https://platform.pennlabs.org/accounts/introspect/',
                            headers=headers,
                            data=body
                        )
                        if data.status_code == 200:  # Access token is valid
                            data = data.json()
                            account = Account.query.filter_by(pennid=data['user']['pennid']).first()
                            return f(account)
                        else:
                            return jsonify({'error': 'Invalid token'}), 401
                    except requests.exceptions.RequestException:  # Can't connect to platform
                        # Throw a 403 because we can't verify the incoming access token so we
                        # treat it as invalid. Ideally platform will never go down, so this
                        # should never happen.
                        return jsonify({'error': 'Unable to connect to Platform'}), 401
            else:
                return jsonify({'error': 'An access token was not provided.'}), 401
        return __auth
    return _auth
