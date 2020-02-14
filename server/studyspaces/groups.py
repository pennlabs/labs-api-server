import requests
from flask import request
from penn.base import APIError


def get_invites_for_account(account, timeout=20):
    """
    Gets a users invites for any gsr groups.
    Return invites along with details about the gsr group (color, name, group id)
    """

    x_authorization = request.headers.get('X-Authorization')
    authorization = request.headers.get('Authorization')

    if not authorization or not x_authorization:
        return None

    headers = {'Authorization': authorization if authorization else x_authorization}
    invite_url = 'https://studentlife.pennlabs.org/users/me/invites'
    try:
        r = requests.get(url=invite_url, headers=headers, timeout=timeout)
    except requests.exceptions.HTTPError as error:
        raise APIError('Server Error: {}'.format(error))
    except requests.exceptions.ConnectTimeout:
        raise APIError('Timeout Error')

    json = r.json()
    return json
