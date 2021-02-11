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

    polls = Poll.query.all()
    polls_query = sqldb.session.query(Poll.id).subquery()

    json_arr = []
    for poll in polls:
        poll_json = get_poll_json(poll, archive)
        json_arr.append(poll_json)
    
    return jsonify({"polls": json_arr})


def get_poll_json(poll, archive):
    poll_json = {
        "id": poll.id,
        "approved": poll.approved,
        "question": poll.question,
        "orgAuthor": poll.source,
        "expiration": poll.expiration
        "options": []
    }

    options = PollOption.query.filter_by(poll=poll.id).all()
    for obj in options:
        if archive:
            poll_json["options"].append({
                "id": obj.id,
                "optionText": obj.choice,
                "votes": PollVote.query.filter_by(choice=obj.id).count(),
                "votesByYear": [
                    {
                        "demographic": "2021",
                        "votes": PollVote.query.filter_by(choice=obj.id, year="2021").count()
                    },
                    {
                        "demographic": "2022",
                        "votes": PollVote.query.filter_by(choice=obj.id, year="2022").count()
                    },
                    {
                        "demographic": "2023",
                        "votes": PollVote.query.filter_by(choice=obj.id, year="2023").count()
                    },
                    {
                        "demographic": "2024",
                        "votes": PollVote.query.filter_by(choice=obj.id, year="2024").count()
                    }
                ],
                "votesBySchool": [
                    {
                        "demographic": "WH",
                        "votes": PollVote.query.filter_by(choice=obj.id, year="WH").count()
                    },
                    {
                        "demographic": "COL",
                        "votes": PollVote.query.filter_by(choice=obj.id, year="COL").count()
                    },
                    {
                        "demographic": "EAS",
                        "votes": PollVote.query.filter_by(choice=obj.id, year="EAS").count()
                    },
                    {
                        "demographic": "NURS",
                        "votes": PollVote.query.filter_by(choice=obj.id, year="NURS").count()
                    }
                ]
            })
        else:
            poll_json["options"].append({
                "id": obj.id,
                "optionText": obj.choice,
                "votes": PollVote.query.filter_by(choice=obj.id).count()
            })
    
    return poll_json

