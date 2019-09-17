import json
import unittest

import server


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
