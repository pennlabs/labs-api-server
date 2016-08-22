from flask import request, Response
from .base import *
from server import app
import requests
import re
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

@app.route('/nso')
def get_nso_events():
    r = requests.get("http://www.nso.upenn.edu/event-calendar.rss")
    split = r.text.split("\n")
    filtered = [i if  "<pubDate" not in i else "<pubDate>Wed, 02 Aug 2016 08:00:00 EST</pubDate>" for i in split]
    output = "\n".join(filtered)
    return Response(output, mimetype="text/xml")
