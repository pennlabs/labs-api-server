import unittest
import server
import json
import datetime


## Fake
authHeaders = [
    ('cookie', '_shibsession_64656661756c7468747470733a2f2f706f6f7272696368617264736c69737448c36f6d2f73686962695c6c657468=_ddb1128649n08aa8e7a462de9970df3e')
]
AUTH_TOKEN = b'5e625cf41e3b7838c79b49d890a203c568a44c3b27362b0a06ab6f08bec8f677'


class MobileAppApiTests(unittest.TestCase):
    def setUp(self):
        server.app.config['TESTING'] = True

    def testDiningVenues(self):
        with server.app.test_request_context():
        # Simple test. Did the request go through?
            venue_data = server.dining.retrieve_venues()
            venue_dict = json.loads(venue_data.data.decode('utf8'))
            venues = venue_dict['document']['venue']
            self.assertTrue(len(venues[0]['venueType']) > 0)

    def testDiningV2Venues(self):
        with server.app.test_request_context():
            venue_res = server.dining.retrieve_venues_v2()
            venue_dict = json.loads(venue_res.data.decode('utf8'))
            self.assertEquals("1920 Commons", venue_dict["document"]["venue"][0]["name"])

    def testDiningV2Menu(self):
        with server.app.test_request_context():
            menu_res = server.dining.retrieve_menu_v2('593', '2016-02-08')
            menu_dict = json.loads(menu_res.data.decode('utf8'))
            self.assertTrue(len(menu_dict["days"][0]["cafes"]["593"]["dayparts"]) > 0)

    def testDiningV2Hours(self):
        with server.app.test_request_context():
            hours_res = server.dining.retrieve_hours_v2('593')
            hours_dict = json.loads(hours_res.data.decode('utf8'))
            self.assertEquals("1920 Commons", hours_dict["cafes"]["593"]["name"])

    def testDiningV2Item(self):
        with server.app.test_request_context():
            item_res = server.dining.retrieve_item_v2('3899220')
            item_dict = json.loads(item_res.data.decode('utf8'))
            self.assertEquals("tomato tzatziki sauce and pita", item_dict["items"]["3899220"]["label"])

    def testDiningWeeklyMenu(self):
        with server.app.test_request_context():
            menu_res = server.dining.retrieve_weekly_menu('593')
            menu_dict = json.loads(menu_res.data.decode('utf8'))
            self.assertTrue("1920 Commons" in menu_dict["Document"]["location"])

    def testDiningDailyMenu(self):
        with server.app.test_request_context():
            menu_res = server.dining.retrieve_daily_menu('593')
            menu_dict = json.loads(menu_res.data.decode('utf8'))
            self.assertEquals("1920 Commons", menu_dict["Document"]["location"])

    def testDirectorySearch(self):
        with server.app.test_request_context('/?name=Zdancewic'):
            res = server.directory.detail_search()
            steve = json.loads(res.data.decode('utf8'))
            self.assertEquals("stevez@cis.upenn.edu", steve["result_data"][0]["list_email"])

    def testDirectoryPersonDetails(self):
        with server.app.test_request_context():
            res = server.directory.person_details("aed1617a1508f282dee235fda2b8c170")
            person_data = json.loads(res.data.decode('utf8'))
            self.assertEquals("STEPHAN A ZDANCEWIC", person_data["detail_name"])

    def testRegistarCourseSearch(self):
        with server.app.test_request_context("/?q=cis 110"):
            res = server.registrar.search()
            course_data = json.loads(res.data.decode('utf8'))
            for val in course_data["courses"]:
                self.assertEquals("110", val["course_number"])

    def testRegistrarCourseSearchNoNumber(self):
        with server.app.test_request_context("/?q=cis"):
            res = server.registrar.search()
            course_data = json.loads(res.data.decode('utf8'))
            for val in course_data["courses"]:
                self.assertEquals("CIS", val["course_department"])

    def testBuildingSearch(self):
        with server.app.test_request_context("/?q=Towne"):
            res = server.buildings.building_search()
            building_data = json.loads(res.data.decode('utf8'))
            self.assertEquals(building_data["result_data"][0]["title"], "Towne")

    def testTransitStopInventory(self):
        with server.app.test_request_context():
            res = json.loads(server.transit.transit_stops().data.decode('utf8'))
            self.assertTrue(len(res["result_data"]) > 0)

# def testTransitBasicRouting(self):
#   with server.app.test_request_context("/?latFrom=39.9529075495845&lonFrom=-75.1925700902939&latTo=39.9447689912513&lonTo=-75.1751947402954"):
#     res = json.loads(server.transit.fastest_route().data.decode('utf8'))['result_data']
#     self.assertEquals("Food Court, 3409 Walnut St.", res['path'][0]['BusStopName'])
#     self.assertEquals("20th & South", res['path'][-1]['BusStopName'])
#     self.assertEquals("PennBUS East", res['route_name'])

    def testLaundryAllHalls(self):
        with server.app.test_request_context():
            res = json.loads(server.laundry.all_halls().data.decode('utf8'))['halls']
            self.assertTrue(len(res) > 50)
            self.assertEquals('Class of 1925 House', res[0]['name'])
            for i, hall in enumerate(res):
                self.assertTrue(hall['dryers_available'] >= 0)
                self.assertTrue(hall['dryers_in_use'] >= 0)
                self.assertTrue(hall['washers_available'] >= 0)
                self.assertTrue(hall['washers_in_use'] >= 0)

    def testLaundryOneHall(self):
        with server.app.test_request_context():
            res = json.loads(server.laundry.hall(26).data.decode('utf8'))
            self.assertEquals(res['hall_name'], 'Harrison-24th FL')

    def testStudyspacesIDs(self):
        with server.app.test_request_context():
            res = json.loads(server.studyspaces.display_id_pairs().data.decode('utf8'))
            self.assertTrue(len(res) > 0)
            for i in res['studyspaces']:
                self.assertTrue(i['id'] > 0)
                self.assertTrue(i['name'] != '')
                self.assertTrue(i['url'] != '')

    def testStudyspaceExtraction(self):
        with server.app.test_request_context():
            d = datetime.datetime.now() + datetime.timedelta(days=1)
            next_date = d.strftime("%Y-%m-%d")
            res = json.loads(server.studyspaces.parse_times(next_date).data.decode('utf8'))
            self.assertTrue(len(res) > 0)
            d2 = res['studyspaces']
            self.assertTrue("building" in d2[0])
            self.assertTrue("start_time" in d2[0])
            self.assertTrue("end_time" in d2[0])
            self.assertTrue("date" in d2[0])
            self.assertTrue("room_name" in d2[0])

    def testWeather(self):
        with server.app.test_request_context():
            res = json.loads(server.weather.retrieve_weather_data().data.decode('utf8'))
            print res
            self.assertTrue(len(res) > 0)
            s = res['weather_data']
            parts = ["base", "clouds", "cod", "coord", "dt", "id", "main", "name",
                     "sys", "visibility", "weather", "wind"]
            for i in parts:
                self.assertTrue(i in s)

    def testAuth(self):
        with server.app.test_request_context(headers=authHeaders):
            authToken = server.auth.auth()
            self.assertEquals(AUTH_TOKEN, authToken)

    def testTokenValidation(self):
        with server.app.test_request_context(headers=authHeaders):
            server.auth.auth()
            res = json.loads(server.auth.validate(AUTH_TOKEN).data.decode('utf8'))
            self.assertEquals(res['status'], 'valid')

    def testInvalidTokenValidation(self):
        with server.app.test_request_context(headers=authHeaders):
            server.auth.auth()
            res = json.loads(server.auth.validate("badtoken").data.decode('utf8'))
            self.assertEquals(res['status'], 'invalid')

    def testTokenValidationNoHttps(self):
        with server.app.test_request_context(headers=authHeaders):
            server.app.config['TESTING'] = False
            server.auth.auth()
            res = json.loads(server.auth.validate(AUTH_TOKEN).data.decode('utf8'))
            self.assertEquals(res['status'], 'insecure access over http')

if __name__ == '__main__':
    unittest.main()
