import mock
import unittest
import server
import json

from server.models import sqldb, StudySpacesBooking


class StudySpacesApiTests(unittest.TestCase):
    def setUp(self):
        server.app.config['TESTING'] = True

    def testStudyspaceBooking(self):
        with server.app.test_client() as c:
            # fake the actual booking
            with mock.patch("penn.studyspaces.StudySpaces.book_room", return_value={"success": "booking placed", "results": True}):
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

    def testStudyspaceCancelFailure(self):
        """Booking cancellation should not succeed if it is not in our database."""

        with server.app.test_client() as c:
            resp = c.post("/studyspaces/cancel", data={
                "booking_id": "definitely_not_a_valid_booking_id_123"
            })
            res = json.loads(resp.data.decode("utf8"))
            self.assertTrue("error" in res)
