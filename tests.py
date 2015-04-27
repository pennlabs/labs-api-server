import unittest
import server
import json


## Fake
authHeaders = [
  ('cookie', '_shibsession_64656661756c7468747470733a2f2f706f6f7272696368617264736c69737448c36f6d2f73686962695c6c657468=_ddb1128649n08aa8e7a462de9970df3e')
]



class MobileAppApiTests(unittest.TestCase):

  def testDiningVenues(self):
    with server.app.test_request_context():
    # Simple test. Did the request go through?
      venue_data = server.dining.retrieve_venues()
      venue_dict = json.loads(venue_data.data)
      venues = venue_dict['document']['venue']
      self.assertTrue(len(venues[0]['venueType']) > 0)

  def testDiningWeeklyMenu(self):
    with server.app.test_request_context():
      menu_res = server.dining.retrieve_weekly_menu('593')
      menu_dict = json.loads(menu_res.data)
      self.assertEquals("University of Pennsylvania 1920 Commons", menu_dict["Document"]["location"])

  def testDiningDailyMenu(self):
    with server.app.test_request_context():
      menu_res = server.dining.retrieve_daily_menu('593')
      menu_dict = json.loads(menu_res.data)
      self.assertEquals("University of Pennsylvania 1920 Commons", menu_dict["Document"]["location"])

  def testDirectorySearch(self):
    with server.app.test_request_context('/?name=Zdancewic'):
      res = server.directory.detail_search()
      steve = json.loads(res.data)
      self.assertEquals("stevez@cis.upenn.edu", steve["result_data"][0]["list_email"])

  def testDirectoryPersonDetails(self):
    with server.app.test_request_context():
      res = server.directory.person_details("aed1617a1508f282dee235fda2b8c170")
      person_data = json.loads(res.data)
      self.assertEquals("STEPHAN A ZDANCEWIC", person_data["detail_name"])

  def testRegistarCourseSearch(self):
    with server.app.test_request_context("/?q=cis 110"):
      res = server.registrar.search()
      course_data = json.loads(res.data)
      for val in course_data["courses"]:
        self.assertEquals("110", val["course_number"])

  def testRegistrarCourseSearchNoNumber(self):
    with server.app.test_request_context("/?q=cis"):
      res = server.registrar.search()
      course_data = json.loads(res.data)
      for val in course_data["courses"]:
        self.assertEquals("CIS", val["course_department"])

  def testBuildingSearch(self):
    with server.app.test_request_context("/?q=Towne"):
      res = server.buildings.building_search()
      building_data = json.loads(res.data)
      self.assertEquals(building_data["result_data"][0]["title"], "Towne")

  def testTransitStopInventory(self):
    with server.app.test_request_context():
      res = json.loads(server.transit.transit_stops().data)
      self.assertTrue(len(res["result_data"]) > 0)

  def testTransitBasicRouting(self):
    with server.app.test_request_context("/?latFrom=39.9529075495845&lonFrom=-75.1925700902939&latTo=39.9447689912513&lonTo=-75.1751947402954"):
      res = json.loads(server.transit.fastest_route().data)['result_data']
      self.assertEquals("Food Court, 3409 Walnut St.", res['path'][0]['BusStopName'])
      self.assertEquals("20th & South", res['path'][-1]['BusStopName'])
      self.assertEquals("PennBUS East", res['route_name'])

  def testLaundryAllHalls(self):
    with server.app.test_request_context():
      res = json.loads(server.laundry.all_halls().data)
      self.assertEquals(res['halls'][0]['hall_no'], 1)

  def testLaundryOneHall(self):
    with server.app.test_request_context():
      res = json.loads(server.laundry.hall(26).data)
      self.assertEquals(res['hall_name'], 'Harrison-24th FL')

  def testAuth(self):
    with server.app.test_request_context(headers=authHeaders):
      authToken = server.auth.auth()
      self.assertEquals('c28cfa2ee70adff8bb84c363fd134b3034d2cd15e88cf2f2ce5f646a10e1344f', authToken)

if __name__ == '__main__':
  unittest.main()