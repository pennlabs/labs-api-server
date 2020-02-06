import datetime
import json
import unittest

import server
from server.models import Account, DiningBalance, sqldb


class DiningApiTests(unittest.TestCase):
    def setUp(self):
        server.app.config['TESTING'] = True

    def testDiningVenues(self):
        with server.app.test_request_context():
            # Simple test. Did the request go through?
            venue_data = server.dining.hours_menus.retrieve_venues()
            venue_dict = json.loads(venue_data.data.decode('utf8'))
            venues = venue_dict['document']['venue']
            self.assertTrue(len(venues[0]['venueType']) > 0)

    def testDiningV2Venues(self):
        with server.app.test_request_context():
            venue_res = server.dining.hours_menus.retrieve_venues_v2()
            venue_dict = json.loads(venue_res.data.decode('utf8'))
            self.assertEquals('1920 Commons',
                              venue_dict['document']['venue'][0]['name'])

    def testDiningV2Menu(self):
        with server.app.test_request_context():
            menu_res = server.dining.hours_menus.retrieve_menu_v2('593', '2016-02-08')
            menu_dict = json.loads(menu_res.data.decode('utf8'))
            self.assertTrue(
                len(menu_dict['days'][0]['cafes']['593']['dayparts']) > 0)

    def testDiningV2Hours(self):
        with server.app.test_request_context():
            hours_res = server.dining.hours_menus.retrieve_hours('593')
            hours_dict = json.loads(hours_res.data.decode('utf8'))
            self.assertEquals('1920 Commons',
                              hours_dict['cafes']['593']['name'])

    def testDiningV2Item(self):
        with server.app.test_request_context():
            item_res = server.dining.hours_menus.retrieve_item_v2('3899220')
            item_dict = json.loads(item_res.data.decode('utf8'))
            self.assertEquals('tomato tzatziki sauce and pita',
                              item_dict['items']['3899220']['label'])

    def testDiningWeeklyMenu(self):
        with server.app.test_request_context():
            menu_res = server.dining.hours_menus.retrieve_weekly_menu('593')
            menu_dict = json.loads(menu_res.data.decode('utf8'))
            self.assertTrue(
                '1920 Commons' in menu_dict['Document']['location'])

    def testDiningDailyMenu(self):
        with server.app.test_request_context():
            menu_res = server.dining.hours_menus.retrieve_daily_menu('593')
            menu_dict = json.loads(menu_res.data.decode('utf8'))
            self.assertEquals('1920 Commons',
                              menu_dict['Document']['location'])

    @classmethod
    def setUpClass(self):
        with server.app.test_request_context():
            dollars = 200
            swipes = 20
            date = datetime.datetime.strptime('2018-09-01', '%Y-%m-%d')
            account = Account(
                id='12345',
                first='Carin',
                last='Gan',
                pennkey='12345',
                email='caringan@penn.edu',
                image_url='test',
                created_at=datetime.datetime.strptime('2018-08-01', '%Y-%m-%d')
            )
            sqldb.session.add(account)
            sqldb.session.commit()
            for x in range(0, 11):
                date = date + datetime.timedelta(days=7)
                item = DiningBalance(
                    account_id='12345',
                    dining_dollars=dollars,
                    swipes=swipes,
                    guest_swipes=1,
                    created_at=date
                )
                sqldb.session.add(item)
                dollars -= 10
                swipes -= 1
            sqldb.session.commit()

    # def testDiningBalances(self):
    #     with server.app.test_client() as c:
    #         res = json.loads(c.get('/dining/balances', headers={'X-Account-ID': '12345'}).data.decode('utf8'))
    #         self.assertEquals(len(res['balance']), 11)
    #         self.assertEquals(res['balance'][0]['dining_dollars'], 200)
    #         self.assertEquals(res['balance'][0]['swipes'], 20)
    #         self.assertEquals(res['balance'][0]['guest_swipes'], 1)
    #         self.assertEquals(res['balance'][9]['dining_dollars'], 110)
    #         self.assertEquals(res['balance'][9]['swipes'], 11)

    # def testDiningBalancesWithParam(self):
    #     with server.app.test_client() as c:
    #         res = json.loads(c.get('/dining/balances?start_date=2018-09-08&end_date=2018-09-30',
    #                          headers={'X-Account-ID': '12345'}).data.decode('utf8'))
    #         self.assertEquals(len(res['balance']), 4)
    #         self.assertEquals(res['balance'][3]['dining_dollars'], 170)
    #         self.assertEquals(res['balance'][3]['swipes'], 17)
    #         self.assertEquals(res['balance'][3]['guest_swipes'], 1)

    # def testDiningProjection(self):
    #     with server.app.test_client() as c:
    #         res = json.loads(c.get('/dining/projection?date=2018-11-17',
    #                          headers={'X-Account-ID': '12345'}).data.decode('utf8'))
    #         self.assertEquals(res['projection']['dining_dollars_day_left'], 71)
    #         self.assertEquals(res['projection']['swipes_day_left'], 71)
