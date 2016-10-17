from flask import Response
from server import app
import requests
import sys
import datetime
sys.setdefaultencoding('utf-8')


@app.route('/nso')
def get_nso_events():
    r = requests.get("http://www.nso.upenn.edu/event-calendar.rss")
    split = r.text.split("\n")
    # TODO: Rework into for-loop
    filtered = [i if "<pubDate" not in i else "<pubDate>" + parseDate(i) + " EST</pubDate>" for i in split]
    filtered = [i if ("<title" not in i or "NSO Event Calendar" in i) else changeTitle(i) for i in filtered]
    output = "\n".join(filtered)
    return Response(output, mimetype="text/xml")


def parseDate(s):
    split = s.split("pubDate")
    s = split[1][1:-8]
    d = datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
    return d.strftime("%a, %d %b %Y %X %Z")


def changeTitle(a):
    index = a.index("event") + 17
    a = subFour(a, index)
    if a[index+6] == '-':
        a = subFour(a, index + 18)
    return a


def subFour(string, index):
    val = string[index:index+6]
    new_val = str((int(val) - 40000 + 240000) % 240000)
    if len(new_val) < 6:
        new_val = "0" + new_val
    if len(new_val) == 2:
        new_val = "000000"
    return string.replace(val, new_val)
