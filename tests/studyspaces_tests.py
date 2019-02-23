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
                self.assertTrue(i['lid'] > 0)
                self.assertTrue('name' in i)
                self.assertTrue('service' in i)

    def testStudyspaceExtraction(self):
        with server.app.test_request_context():
            res = json.loads(
                server.studyspaces.parse_times(2683).data.decode('utf8'))
            self.assertTrue(len(res) > 0)
            self.assertTrue("id" in res)
            self.assertTrue("categories" in res)

    def testStudyspaceLegacySupport(self):
        with server.app.test_request_context():
            res = json.loads(server.studyspaces.parse_times(2683).data.decode('utf8'))
            self.assertTrue("location_id" in res)
            self.assertTrue("rooms" in res)
            for room in res["rooms"]:
                self.assertTrue("room_id" in room)
                self.assertTrue("gid" in room)
                self.assertTrue("lid" in room)

    def testStudyspaceBooking(self):
        with server.app.test_client() as c:
            # fake the actual booking
            with mock.patch("penn.studyspaces.StudySpaces.book_room", return_value={"success": "booking placed", "results": []}):
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
                }, headers={"X-Device-Id": "test"})
            res = json.loads(resp.data.decode("utf8"))
            self.assertTrue(len(res) > 0)

            # make sure the booking is saved to the database
            self.assertEquals(sqldb.session.query(StudySpacesBooking).count(), 1)

            # check to make sure user is saved
            self.assertTrue(sqldb.session.query(StudySpacesBooking).first().user is not None)

    def testStudyspaceCancelFailure(self):
        """Booking cancellation should not succeed if it is not in our database."""

        with server.app.test_client() as c:
            resp = c.post("/studyspaces/cancel", data={
                "booking_id": "definitely_not_a_valid_booking_id_123"
            })
            res = json.loads(resp.data.decode("utf8"))
            self.assertTrue("error" in res)
