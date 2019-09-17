import json
import unittest

import server


# Fake
authHeaders = [(
    'cookie',
    '_shibsession_64656661756c7468747470733a2f2f706f6f7272696368617264736c69737448c36f6d2f73686962695c6c657468=_ddb1128649n08aa8e7a462de9970df3e'
)]
AUTH_TOKEN = b'5e625cf41e3b7838c79b49d890a203c568a44c3b27362b0a06ab6f08bec8f677'


class AuthApiTests(unittest.TestCase):
    def setUp(self):
        server.app.config['TESTING'] = True

    def testAuth(self):
        with server.app.test_request_context(headers=authHeaders):
            authToken = server.auth.auth()
            self.assertEquals(AUTH_TOKEN, authToken)

    def testTokenValidation(self):
        with server.app.test_request_context(headers=authHeaders):
            server.auth.auth()
            res = json.loads(
                server.auth.validate(AUTH_TOKEN).data.decode('utf8'))
            self.assertEquals(res['status'], 'valid')

    def testInvalidTokenValidation(self):
        with server.app.test_request_context(headers=authHeaders):
            server.auth.auth()
            res = json.loads(
                server.auth.validate('badtoken')[0].data.decode('utf8'))
            self.assertEquals(res['status'], 'invalid')

    def testTokenValidationNoHttps(self):
        with server.app.test_request_context(headers=authHeaders):
            server.app.config['TESTING'] = False
            server.auth.auth()
            res = json.loads(
                server.auth.validate(AUTH_TOKEN)[0].data.decode('utf8'))
            self.assertEquals(res['status'], 'insecure access over http')
