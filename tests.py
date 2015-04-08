import unittest
import server
import json

class MobileAppApiTests(unittest.TestCase):

  def testDiningVenues(self):
    with server.app.test_request_context():
    # Simple test. Did the request go through?
      venue_data = server.dining.retrieve_venues()
      venue_dict = json.loads(venue_data.data)
      print venue_dict
      venues = venue_dict['result_data']['document']['venue']
      print venues
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
    with server.app.test_request_context("/?latFrom=39.9546024&lonFrom=-75.1838311&latTo=39.9538555&lonTo=-75.2200868"):
      res = json.loads(server.transit.fastest_route().data)
      self.assertEquals("DRL, 200 S 33rd St.", res['fromStop']['BusStopName'])
      self.assertEquals("48th & Spruce", res['toStop']['BusStopName'])

  def testLaundryAllHalls(self):
    with server.app.test_request_context():
      res = json.loads(server.laundry.all_halls().data)
      self.assertEquals(res['halls'][0]['hall_no'], 1)

  def testLaundryOneHall(self):
    with server.app.test_request_context():
      res = json.loads(server.laundry.hall(26).data)
      self.assertEquals(res['hall_name'], 'Harrison-24th FL')

if __name__ == '__main__':
  unittest.main()