from flask import request, jsonify
from server import app, sqldb
from .models import PostAccount, Post, PostFilter, PostStatus
import json
import datetime


@app.route('/portal/post/new', methods=['POST'])
def create_post():
    account_id = request.form.get("account_id")
    if not account_id:
        return jsonify({"error": "No account provided."}), 400

    try:
        account = PostAccount.get_account(account_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    source = request.form.get("source")
    title = request.form.get("title")
    subtitle = request.form.get("subtitle")
    time_label = request.form.get("time_label")
    post_url = request.form.get("post_url")
    image_url = request.form.get("image_url")
    filters_str = request.form.get("filters")

    start_date_str = request.form.get("start_date")
    end_date_str = request.form.get("end_date")

    if any(x is None for x in [image_url, start_date_str, end_date_str]):
        return jsonify({"error": "Parameter is missing"}), 400

    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S')
    end_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S')

    if filters_str:
        filters = filters_str.split(',')
    else:
        filters = None

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

    return jsonify({"post_id": post.id})


@app.route('/portal/account/new', methods=['POST'])
def create_account():
    name = request.form.get("name")
    email = request.form.get("email")
    encrypted_password = request.form.get("encrypted_password")

    if any(x is None for x in [name, email, encrypted_password]):
        return jsonify({"error": "Parameter is missing"}), 400

    account = PostAccount(name=name, email=email, encrypted_password=encrypted_password)
    sqldb.session.add(account)
    sqldb.session.commit()

    return jsonify({'account_id': account.id})


@app.route('/portal/post/update', methods=['POST'])
def update_post():
    try:
        account_id = request.form.get("account_id")
        account = PostAccount.get_account(account_id)
        post_id = request.form.get("post_id")
        post = Post.get_post(post_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if post.account != account.id:
        return jsonify({"error": "Account not authorized to update this post."}), 400

    source = request.form.get("source")
    title = request.form.get("title")
    subtitle = request.form.get("subtitle")
    time_label = request.form.get("time_label")
    post_url = request.form.get("post_url")
    image_url = request.form.get("image_url")
    filters_str = request.form.get("filters")

    start_date_str = request.form.get("start_date")
    end_date_str = request.form.get("end_date")

    if any(x is None for x in [image_url, start_date_str, end_date_str]):
        return jsonify({"error": "Parameter is missing"}), 400

    post.source = request.form.get("source")
    post.title = request.form.get("title")
    post.subtitle = request.form.get("subtitle")
    post.time_label = request.form.get("time_label")
    post.post_url = request.form.get("post_url")
    post.image_url = request.form.get("image_url")
    post.filters_str = request.form.get("filters")

    post.start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S')
    post.end_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S')

    PostFilter.query.filter_by(post=post.id).delete()
    if filters_str:
        post.filters = True
        filters = filters_str.split(',')
        for filter_str in filters:
            post_filter = PostFilter(post=post.id, type=filter_str)
            sqldb.session.add(post_filter)
    else:
        post.filters = False

    status = PostStatus(post=post.id, status="updated")
    sqldb.session.add(status)
    sqldb.session.commit()

    return jsonify({"post_id": post.id})
