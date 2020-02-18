import datetime
import json
import unittest

import server


class MobileAppApiTests(unittest.TestCase):
    def setUp(self):
        server.app.config['TESTING'] = True

    def testDirectorySearch(self):
        with server.app.test_request_context('/?name=Zdancewic'):
            res = server.directory.detail_search()
            steve = json.loads(res.data.decode('utf8'))
            self.assertEquals('stevez@cis.upenn.edu',
                              steve['result_data'][0]['list_email'])

    def testDirectoryPersonDetails(self):
        with server.app.test_request_context():
            res = server.directory.person_details(
                'aed1617a1508f282dee235fda2b8c170')
            person_data = json.loads(res.data.decode('utf8'))
            self.assertEquals('STEPHAN A ZDANCEWIC',
                              person_data['detail_name'])

    def testRegistarCourseSearch(self):
        with server.app.test_request_context('/?q=cis 110'):
            res = server.registrar.search()
            course_data = json.loads(res.data.decode('utf8'))
            for val in course_data['courses']:
                self.assertEquals('110', val['course_number'])

    def testRegistrarCourseSearchNoNumber(self):
        with server.app.test_request_context('/?q=cis'):
            res = server.registrar.search()
            course_data = json.loads(res.data.decode('utf8'))
            for val in course_data['courses']:
                self.assertEquals('CIS', val['course_department'])

    # def testTransitStopInventory(self):
    #     with server.app.test_request_context():
    #         res = json.loads(server.transit.transit_stops().data.decode(
    #             'utf8'))
    #         self.assertTrue(len(res['result_data']) > 0)

    # def testTransitBasicRouting(self):
    #     query = '/?latFrom=39.9529075495845&lonFrom=-75.1925700902939&latTo=39.9447689912513&lonTo=-75.1751947402954'
    #     with server.app.test_request_context(query):
    #         res = json.loads(server.transit.fastest_route().data.decode('utf8'))
    #         self.assertEquals(res['Error'], 'We couldn't find a helpful Penn Transit route for those locations.')

    def testWeather(self):
        with server.app.test_request_context():
            res = json.loads(server.weather.retrieve_weather_data()
                             .data.decode('utf8'))
            self.assertTrue(len(res) > 0)
            s = res['weather_data']
            self.assertTrue('clouds' in s)
            self.assertTrue('name' in s)
            self.assertTrue('coord' in s)
            self.assertTrue('sys' in s)
            self.assertTrue('base' in s)
            self.assertTrue('visibility' in s)
            self.assertTrue('cod' in s)
            self.assertTrue('weather' in s)
            self.assertTrue('dt' in s)
            self.assertTrue('main' in s)
            self.assertTrue('id' in s)
            self.assertTrue('wind' in s)

    # def testFitness(self):
    #     with server.app.test_request_context():
    #         resp = json.loads(server.fitness.fitness_usage().data.decode('utf8'))
    #         self.assertTrue(len(resp['results']) > 0)
    #         for location in resp['results']:
    #             self.assertTrue('updated' in location)

    def testCalendarToday(self):
        with server.app.test_request_context():
            res = json.loads(server.calendar3year.pull_today().data.decode(
                'utf8'))
            s = res['calendar']
            today = datetime.datetime.now().date()
            for event in s:
                self.assertTrue('end' in event)
                self.assertTrue('name' in event)
                self.assertTrue('start' in event)
                d = datetime.datetime.strptime(event['start'],
                                               '%Y-%m-%d').date()
                self.assertTrue((d - today).total_seconds() <= 1209600)

    def testCalendarDate(self):
        with server.app.test_request_context():
            ind = '2017-01-01'
            chosen_date = datetime.date(2017, 1, 1)
            res = json.loads(
                server.calendar3year.pull_date(ind).data.decode('utf8'))
            s = res['calendar']
            for event in s:
                self.assertTrue('end' in event)
                self.assertTrue('name' in event)
                self.assertTrue('start' in event)
                d = datetime.datetime.strptime(event['start'],
                                               '%Y-%m-%d').date()
                self.assertTrue((d - chosen_date).total_seconds() <= 1209600)
