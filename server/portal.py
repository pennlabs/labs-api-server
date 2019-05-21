from flask import request, jsonify
from server import app, sqldb
from .models import PostAccount, Post, PostFilter, PostStatus
import json
import datetime


@app.route('/post/new', methods=['POST'])
def create_post():
    account_id = request.forms.get("account_id")
    if not post_account_id:
        return jsonify({'success': False, "error": "No account provided."}), 400

    try:
        account = PostAccount.get_account(account_id)
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    source = requests.form.get("source")
    title = requests.form.get("title")
    subtitle = requests.form.get("subtitle")
    time_label = requests.form.get("time_label")
    post_url = requests.form.get("post_url")
    image_url = requests.form.get("image_url")
    filters_str = requests.form.get("filters")

    start_date_str = requests.form.get("start_date")
    end_date_str = requests.form.get("end_date")

    if any(x is None for x in [image_url, start_date_str, end_date_str]):
        raise KeyError("Parameter is missing")

    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S')
    end_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S')

    if filters_str:
        filters = filters_str.split(',')
    else:
        filters = None

    source = sqldb.Column(sqldb.Text, nullable=True)
    title = sqldb.Column(sqldb.Text, nullable=True)
    subtitle = sqldb.Column(sqldb.Text, nullable=True)
    time_label = sqldb.Column(sqldb.Text, nullable=True)
    post_url = sqldb.Column(sqldb.Text, nullable=True)
    image_url = sqldb.Column(sqldb.Text, nullable=False)
    filters = sqldb.Column(sqldb.Boolean, default=False)
    start_date = sqldb.Column(sqldb.DateTime, nullable=False)
    end_date = sqldb.Column(sqldb.DateTime, nullable=False)

    post = Post(account=account.id, source=source, title=title, subtitle=subtitle, time_label=time_label, post_url=post_url, 
                image_url=image_url, start_date=start_date, end_date=end_date, filters=(True if filters else False))
    sqldb.session.add(post)
    sqldb.session.commit()

    if filters:
        for filter_str in filters:
            post_filter = PostFilter(post=post.id, type=filter_str)
            sqldb.session.add(post_filter)

    status = PostStatus(post=post.id, status="submitted")
    sqldb.session.add(status)
	sqldb.session.commit()

    return jsonify({'success': True, "error": None})
