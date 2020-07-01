from flask import jsonify, request
from sqlalchemy import and_

from server import app
from server.models import Account


@app.route("/studyspaces/user/search", methods=["GET"])
def get_nam():
    """
    Gets users that match search query
    """

    query = request.args.get("query")
    if not query:
        return jsonify({"error": "Query argument not found."}), 400

    if len(query) <= 1:
        return jsonify({"error": "Query is too short. Minimum length is two characters."}), 400

    first = None
    last = None
    if " " in query:
        split = query.split(" ")
        if len(split) >= 2:
            first = split[0]
            last = split[1]

    users = []
    if first and last:
        and_matches = Account.query.filter(
            and_(Account.first.like("{}%".format(first)), Account.last.like("{}%".format(last)))
        ).all()
        users.extend(and_matches)

        if not users:
            first_letter_matches_and_last_name = Account.query.filter(
                and_(
                    Account.first.like("{}%".format(first[:1])),
                    Account.last.like("{}%".format(last)),
                )
            ).all()
            users.extend(first_letter_matches_and_last_name)

            last_name_matches = Account.query.filter(Account.last.like("{}%".format(last))).all()
            last_name_matches = sorted(last_name_matches, key=lambda x: x.first)
            users.extend(last_name_matches)
    else:
        starting_query = "{}%".format(query)
        general_query = "%{}%".format(query)

        starting_exact_matches = Account.query.filter(Account.first.like(query)).all()
        starting_exact_matches = sorted(starting_exact_matches, key=lambda x: x.last)

        starting_first_name_matches = Account.query.filter(Account.first.like(starting_query)).all()
        starting_first_name_matches = sorted(starting_first_name_matches, key=lambda x: x.last)

        starting_last_name_matches = Account.query.filter(Account.last.like(starting_query)).all()
        general_first_name_matches = Account.query.filter(Account.first.like(general_query)).all()
        general_last_name_matches = Account.query.filter(Account.last.like(general_query)).all()

        users.extend(starting_exact_matches)
        users.extend(starting_first_name_matches)
        users.extend(starting_last_name_matches)
        users.extend(general_first_name_matches)
        users.extend(general_last_name_matches)

    if not users:
        # If no users found by search first or last name, search the pennkey
        starting_pennkey_matches = Account.query.filter(
            Account.pennkey.like("{}%".format(query))
        ).all()
        general_pennkey_matches = Account.query.filter(
            Account.pennkey.like("%{}%".format(query))
        ).all()

        users.extend(starting_pennkey_matches)
        users.extend(general_pennkey_matches)

    seen_pennkeys = set()
    filtered_users = []
    for user in users:
        if user.pennkey not in seen_pennkeys:
            filtered_users.append(user)
            seen_pennkeys.add(user.pennkey)

    filtered_users = [
        {"first": x.first, "last": x.last, "pennkey": x.pennkey, "email": x.email, }
        for x in filtered_users
    ]

    return jsonify({"results": filtered_users})
