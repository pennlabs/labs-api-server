from datetime import datetime

from flask import jsonify, request

from server import app, sqldb
from server.models import Poll, PollOption


"""
Endpoint: /api/polls
HTTP Methods: POST
Response Formats: JSON
Content-Type: application/json
Parameters: question, orgAuthor, expiration, options

Creates new poll
If successful, returns poll ID
"""


@app.route("/api/polls", methods=["POST"])
def create_poll():
    data = request.get_json()

    question = data.get("question")
    organization = data.get("orgAuthor")
    expiration_str = data.get("expiration")
    options = list(data.get("options"))

    if any(x is None for x in [question, organization, expiration_str, options]):
        return jsonify({"error": "Parameter is missing"}), 400

    expiration = datetime.strptime(expiration_str, "%Y-%m-%dT%H:%M:%S")

    poll = Poll(
        question=question,
        source=organization,
        expiration=expiration
    )
    sqldb.session.add(poll)
    sqldb.session.commit()

    for option_str in options:
        poll_option = PollOption(poll=poll.id, choice=option_str)
        sqldb.session.add(poll_option)

    sqldb.session.commit()

    return jsonify({"poll_id": poll.id})


"""
Endpoint: /api/polls/<poll_id>
HTTP Methods: PUT
Response Formats: JSON
Content-Type: application/json
Parameters: question, orgAuthor, expiration, options

Updates existing poll
If successful, returns bool
"""


"""@app.route("/api/polls/<int:poll_id>", methods=["PUT"])
def update_poll():
    data = request.get_json()
    poll = Poll.query.filter_by(id=poll_id).first()
    if not poll:
        return jsonify({"error": "Poll not found."}), 400

    question = data.get("question")
    organization = data.get("orgAuthor")
    expiration_str = data.get("expiration")
    options = list(data.get("options"))

    if all(x is None for x in [question, organization, expiration_str, options]):
        return jsonify({"error": "Must provide parameter to update"})

    if question:
        poll.question = question

    if organization:
        poll.source = organization

    if expiration_str:
        expiration = datetime.strptime(expiration_str, "%Y-%m-%dT%H:%M:%S")
        poll.expiration = expiration

    if options:
        PollOption.query.filter_by(poll=poll.id).delete()
        PollVote.query.filter_by(poll=poll.id).delete()
        for option_str in options:
            poll_option = PollOption(poll=poll.id, choice=option_str)
            sqldb.session.add(poll_option)

        sqldb.session.commit()

    return jsonify({"success": True})"""


"""
Endpoint: /api/polls/<poll_id>
HTTP Methods: DELETE
Response Formats: JSON
Content-Type: application/json

Deletes existing poll
If successful, returns bool
"""


"""@app.route("/api/polls/<int:poll_id>", methods=["DELETE"])
def update_poll():
    poll = Poll.query.filter_by(id=poll_id).first()
    if not poll:
        return jsonify({"error": "Poll not found."}), 400

    Poll.query.filter_by(id=poll.id).delete()
    PollOption.query.filter_by(poll=poll.id).delete()
    PollVote.query.filter_by(poll=poll.id).delete()

    return jsonify({"success": True})"""
