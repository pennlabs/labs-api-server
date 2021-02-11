import os
import uuid
from datetime import datetime

from flask import jsonify, request
from pytz import timezone
from sqlalchemy import and_, desc, func

from server import app, sqldb
from server.models import (Poll, PollOption, PollVote)

"""
Endpoint: /api/choosePollOption
HTTP Methods: POST
Response Formats: JSON
Content-Type: application/json
Parameters: poll_id, option_id, school, year

Adds new vote
If successful, returns poll ID
"""
@app.route("/api/choosePollOption", methods=["POST"])
def add_vote():
    data = request.get_json()

    poll = Poll.query.filter_by(id=data.get("poll_id")).first()
    opt = PollOption.query.filter_by(id=data.get("option_id")).first()

    if not poll:
        return jsonify({"error": "Poll not found."}), 400
    if not opt:
        return jsonify("error": "Poll option not found."), 400

    poll_id = data.get("poll_id")
    choice = data.get("option_id")
    school = data.get("school")
    year = data.get("year")

    if any(x is None for x in [poll_id, option_id, school, year]):
        return jsonify({"error": "Parameter is missing"}), 400

    poll_vote = PollVote(
        poll=poll_id,
        choice=choice,
        school=school,
        year=year
    )
    sqldb.session.add(poll_vote)
    sqldb.session.commit()

    return jsonify({"poll_id": poll.id})