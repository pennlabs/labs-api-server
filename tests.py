import unittest
from server.penndata import *
import server.api
import json


class MobileAppApiTests(unittest.TestCase):

  def testVenues(self):
    with server.api.app.test_request_context():
      # Simple test. Did the request go through?
      venue_data = server.api.retrieve_venues()
      venue_dict = json.loads(venue_data.data)
      venues = venue_dict['document']['venue']
      self.assertTrue(len(venues[0]['venueType']) > 0)

  def testWeeklyMenu(self):
    with server.api.app.test_request_context():
      menu_res = server.api.retrieve_weekly_menu('593')
      menu_dict = json.loads(menu_res.data)
      self.assertEquals("University of Pennsylvania 1920 Commons",
                        menu_dict["Document"]["location"])

  def testDailyMenu(self):
    with server.api.app.test_request_context():
      menu_res = server.api.retrieve_daily_menu('593')
      menu_dict = json.loads(menu_res.data)
      self.assertEquals("University of Pennsylvania 1920 Commons",
                        menu_dict["Document"]["location"])

  def testDirectorySearch(self):
    with server.api.app.test_request_context('/?name=Zdancewic'):
      res = server.api.detail_search()
      steve = json.loads(res.data)
      self.assertEquals("stevez@cis.upenn.edu",
                        steve["result_data"][0]["list_email"])

  def testPersonDetails(self):
    with server.api.app.test_request_context():
      res = server.api.person_details("aed1617a1508f282dee235fda2b8c170")
      person_data = json.loads(res.data)
      self.assertEquals("STEPHAN A ZDANCEWIC", person_data["detail_name"])

  def testCourseSearchQuery(self):
    with server.api.app.test_request_context("/?q=cis 110"):
      res = server.api.search()
      course_data = json.loads(res.data)
      for val in course_data["courses"]:
        self.assertEquals("110", val["course_number"])

  def testCourseSearchQuery(self):
    with server.api.app.test_request_context("/?q=cis"):
      res = server.api.search()
      course_data = json.loads(res.data)
      for val in course_data["courses"]:
        self.assertEquals("CIS", val["course_department"])

if __name__ == '__main__':
  unittest.main()
