import os
import uuid
from datetime import datetime

from flask import jsonify, request
from pytz import timezone
from sqlalchemy import and_, desc, func

from server import app, sqldb
from server.models import (Poll, PollOption, PollVote)


"""
Endpoint: /api/polls
HTTP Methods: GET
Response Formats: JSON
Parameters: account

Returns list of polls
"""
@app.route("/api/polls", methods=["GET"])
def get_all_polls():
    archive = request.args.get("archives")
    email = request.args.get("email")

    polls = Poll.query.all()
    votes = PollVote.query.filter_by(email=email).all()
    now = datetime.now(est).replace(tzinfo=None)

    json_arr = []
    if not email or not votes:
        for poll in polls:
            if archive and now > poll.expiration:
                poll_json = get_poll_json(poll)
                json_arr.append(poll_json)
            else:
                if poll.expiration >= now:
                    poll_json = get_poll_json(poll)
                    json_arr.append(poll_json)
    else:
        for vote in votes:
            poll = Poll.query.filter_by(id=vote.poll).first()
            if archive and now > poll.expiration:
                poll_json = get_poll_json(poll)
                poll_json["optionChosen"] = vote.choice
                json_arr.append(poll_json)
            else:
                if poll.expiration >= now:
                    poll_json = get_poll_json(poll)
                    poll_json["optionChosen"] = vote.choice
                    json_arr.append(poll_json)
    
    return jsonify({"polls": json_arr})

def get_poll_json(poll):
    poll_json = {
        "id": poll.id,
        "approved": poll.approved,
        "question": poll.question,
        "orgAuthor": poll.source,
        "expiration": poll.expiration,
        "optionChosen": None,
        "options": []
    }
    options = PollOption.query.filter_by(poll=poll.id).all()
    for obj in options:
        poll_json["options"].append({
            "id": obj.id,
            "optionText": obj.choice,
            "votes": PollVote.query.filter_by(choice=obj.id).count(),
            "votesByYear": [
                {
                    "demographic": "year_3",
                    "votes": PollVote.query.filter_by(choice=obj.id, year="2021").count()
                },
                {
                    "demographic": "year_2",
                    "votes": PollVote.query.filter_by(choice=obj.id, year="2022").count()
                },
                {
                    "demographic": "year_1",
                    "votes": PollVote.query.filter_by(choice=obj.id, year="2023").count()
                },
                {
                    "demographic": "year_0",
                    "votes": PollVote.query.filter_by(choice=obj.id, year="2024").count()
                }
            ],
            "votesBySchool": [
                {
                    "demographic": "WH",
                    "votes": PollVote.query.filter_by(choice=obj.id, school="WH").count()
                },
                {
                    "demographic": "COL",
                    "votes": PollVote.query.filter_by(choice=obj.id, school="COL").count()
                },
                {
                    "demographic": "EAS",
                    "votes": PollVote.query.filter_by(choice=obj.id, school="EAS").count()
                },
                {
                    "demographic": "NURS",
                    "votes": PollVote.query.filter_by(choice=obj.id, school="NURS").count()
                }
            ]
        })

    
    return poll_json

