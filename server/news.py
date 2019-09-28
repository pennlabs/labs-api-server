import requests
from bs4 import BeautifulSoup
from flask import jsonify
from requests.exceptions import ConnectionError

from server import app


BASE_URL = 'https://www.thedp.com/'


@app.route('/news/', methods=['GET'])
def fetch_news_article():
    article = fetch_frontpage_article()
    if article:
        return jsonify({'article': article})
    else:
        return jsonify({'error': 'Site could not be reached or could not be parsed.'})


def fetch_frontpage_article():
    """Returns a list of articles."""
    try:
        url = BASE_URL
        resp = requests.get(url)
    except ConnectionError:
        return None

    html = resp.content.decode('utf8')

    soup = BeautifulSoup(html, 'html5lib')

    frontpage = soup.find('div', {'class': 'col-lg-6 col-md-5 col-sm-12 frontpage-carousel'})
    if frontpage:
        title_html = frontpage.find('a', {'class': 'frontpage-link large-link'})
    if title_html:
        link = title_html['href']
        title = title_html.get_text()

    subtitle_html = frontpage.find('p')
    if subtitle_html:
        subtitle = subtitle_html.get_text()

    timestamp_html = frontpage.find('div', {'class': 'timestamp'})
    if timestamp_html:
        timestamp = timestamp_html.get_text()

    image_html = frontpage.find('img')
    if image_html:
        imageurl = image_html['src']

    if all(v is not None for v in [title, subtitle, timestamp, imageurl, link]):
        article = {
            'source': 'The Daily Pennsylvanian',
            'title': title,
            'subtitle': subtitle,
            'timestamp': timestamp,
            'image_url': imageurl,
            'article_url': link,
        }
        return article
    else:
        return None
