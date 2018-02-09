import mock
import unittest
import server
import json

from server.models import sqldb, StudySpacesBooking


class StudySpacesApiTests(unittest.TestCase):
    def setUp(self):
        server.app.config['TESTING'] = True

    def testStudyspacesIDs(self):
        with server.app.test_request_context():
            res = json.loads(server.studyspaces.display_id_pairs().data.decode(
                'utf8'))
            self.assertTrue(len(res) > 0)
            for i in res['locations']:
                self.assertTrue(i['id'] > 0)
                self.assertTrue(i['name'])
                self.assertTrue(i['service'])

    def testStudyspaceExtraction(self):
        with server.app.test_request_context():
            res = json.loads(
                server.studyspaces.parse_times(2683).data.decode('utf8'))
            self.assertTrue(len(res) > 0)
            self.assertTrue("date" in res)
            self.assertTrue("location_id" in res)
            self.assertTrue("rooms" in res)

    def testStudyspaceBooking(self):
        with server.app.test_client() as c:
            # fake the actual booking
            with mock.patch("penn.studyspaces.StudySpaces.book_room", return_value=True):
                resp = c.post("/studyspaces/book", data={
                    "building": 1,
                    "room": 1,
                    "start": "2017-02-08 10:00:00",
                    "end": "2017-02-08 10:30:00",
                    "firstname": "Test",
                    "lastname": "Test",
                    "email": "test@example.com",
                    "groupname": "Testing",
                    "phone": "000-000-0000",
                    "size": 1
                })
            res = json.loads(resp.data.decode("utf8"))
            self.assertTrue(len(res) > 0)
            self.assertTrue(res["results"], res)

            # make sure the booking is saved to the database
            self.assertEquals(sqldb.session.query(StudySpacesBooking).count(), 1)
