import unittest
import mock
import server
import json
import datetime

from server.models import sqldb, LaundrySnapshot


class LaundryApiTests(unittest.TestCase):
    def setUp(self):
        server.app.config['TESTING'] = True

    @classmethod
    def setUpClass(self):
        with server.app.test_request_context():
            for x in range(0, 24 * 60, 60):
                item = LaundrySnapshot(
                    date=datetime.date(2017, 1, 1),
                    time=x,
                    room=1,
                    washers=3,
                    dryers=3,
                    total_washers=3,
                    total_dryers=3
                )
                sqldb.session.add(item)
            for x in range(0, 24 * 60, 60):
                item = LaundrySnapshot(
                    date=datetime.date(2017, 1, 1) - datetime.timedelta(days=7),
                    time=x,
                    room=1,
                    washers=0,
                    dryers=0,
                    total_washers=3,
                    total_dryers=3
                )
                sqldb.session.add(item)
            sqldb.session.commit()

    def fakeLaundryGet(url, *args, **kwargs):
        if "suds.kite.upenn.edu" in url:
            with open("tests/laundry_snapshot.html", "rb") as f:
                m = mock.MagicMock(content=f.read())
            return m
        else:
            raise NotImplementedError

    @mock.patch("penn.laundry.requests.get", fakeLaundryGet)
    def testLaundryAllHalls(self):
        with server.app.test_request_context():
            res = json.loads(server.laundry.all_halls().data.decode('utf8'))[
                'halls']
            self.assertTrue(len(res) > 45)
            self.assertTrue('English House' in res)
            for info in res.values():
                for t in ['washers', 'dryers']:
                    self.assertTrue(info[t]['running'] >= 0)
                    self.assertTrue(info[t]['offline'] >= 0)
                    self.assertTrue(info[t]['out_of_order'] >= 0)
                    self.assertTrue(info[t]['open'] >= 0)

    @mock.patch("requests.get", fakeLaundryGet)
    def testLaundryOneHall(self):
        with server.app.test_request_context():
            res = json.loads(server.laundry.hall(26).data.decode('utf8'))
            self.assertEquals(res['hall_name'], 'Harrison Floor 20')

    def testLaundryUsage(self):
        with server.app.test_request_context():
            request = server.laundry.usage(20, 2017, 1, 1)
            res = json.loads(request.data.decode('utf8'))
            self.assertEquals(res['hall_name'], 'Harrison Floor 08')
            self.assertEquals(res['location'], 'Harrison')
            self.assertEquals(res['day_of_week'], 'Sunday')
            self.assertEquals(res['end_date'], '2017-01-01')
            self.assertEquals(len(res['washer_data']), 27)
            self.assertEquals(len(res['dryer_data']), 27)

    def testLaundryDatabase(self):
        with server.app.test_request_context():
            request = server.laundry.usage(1, 2017, 1, 1)
            res = json.loads(request.data.decode('utf8'))
            self.assertEquals(res['total_number_of_washers'], 3)
            self.assertEquals(res['total_number_of_dryers'], 3)
            for x in range(0, 23):
                self.assertEquals(res['washer_data'][str(x)], 1.5)
                self.assertEquals(res['dryer_data'][str(x)], 1.5)
