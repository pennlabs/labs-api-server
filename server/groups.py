import requests
from flask import request


def get_invites_for_account(account):
    if account:
        x_authorization = request.headers.get('X-Authorization')
        authorization = request.headers.get('Authorization')

        headers = {'Authorization': authorization if authorization else x_authorization}
        invite_url = 'https://studentlife.pennlabs.org/users/{}/invites'.format(account.pennkey)
        r = requests.get(url=invite_url, headers=headers)
        json = r.json()
        return json
    return list()
