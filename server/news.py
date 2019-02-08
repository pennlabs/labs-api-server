import datetime
import requests

from server import app
from bs4 import BeautifulSoup

from flask import jsonify
from requests.exceptions import HTTPError

BASE_URL = "https://www.thedp.com/"


@app.route('/news/', methods=['GET'])
def fetch_news():
	article = fetch_frontpage_article()
	return jsonify({"articles": [article]})

def fetch_frontpage_article():
	"""Returns a list of articles."""
	url = BASE_URL
	resp = requests.get(url)
	html = resp.content.decode("utf8")

	soup = BeautifulSoup(html, "html5lib")

	frontpage = soup.find("div", {'class': "col-lg-6 col-md-5 col-sm-12 frontpage-carousel"})
	title_html = frontpage.find("a", {'class': "frontpage-link large-link"})
	link = title_html["href"]
	title = title_html.get_text()
	subtitle = frontpage.find("p").get_text()
	timestamp = frontpage.find("div", {'class': "timestamp"}).get_text()
	imageurl = frontpage.find("img")["src"]

	article = {
		'title': title,
		'subtitle': subtitle,
		'timestamp': timestamp,
		'imageurl': imageurl,
	}
	return article
