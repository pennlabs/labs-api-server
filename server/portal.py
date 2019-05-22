from flask import request, jsonify
from server import app, sqldb
from .models import PostAccount, Post, PostFilter, PostStatus
from sqlalchemy import desc
import json
import datetime


"""
Example: JSON Encoding
{
    "account_id": "7900fffd-0223-4381-a61d-9a16a24ca4b7",
    "image_url": "https://i.imgur.com/CmhAG25.jpg",
    "post_url": "https://pennlabs.org/",
    "source": "Penn Labs",
    "subtitle": "A small subtitle",
    "time_label": "Today",
    "title": "Testing a new feature!",
    "start_date": "2019-05-23T08:00:00",
    "end_date": "2019-05-24T00:00:00",
    "filters": [
        {
            "type": "class",
            "filter": "2020"
        },
        {
            "type": "class",
            "filter": "2021"
        },
        {
            "type": "major",
            "filter": "CIS"
        }
    ]
}
"""


@app.route('/portal/post/new', methods=['POST'])
def create_post():
    data = request.get_json()

    try:
        account_id = data.get("account_id")
        account = PostAccount.get_account(account_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    source = data.get("source")
    title = data.get("title")
    subtitle = data.get("subtitle")
    time_label = data.get("time_label")
    post_url = data.get("post_url")
    image_url = data.get("image_url")
    filters = list(data.get("filters"))

    start_date_str = data.get("start_date")
    end_date_str = data.get("end_date")

    if any(x is None for x in [image_url, start_date_str, end_date_str]):
        return jsonify({"error": "Parameter is missing"}), 400

    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S')
    end_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S')

    post = Post(account=account.id, source=source, title=title, subtitle=subtitle, time_label=time_label, post_url=post_url, 
                image_url=image_url, start_date=start_date, end_date=end_date, filters=(True if filters else False))
    sqldb.session.add(post)
    sqldb.session.commit()

    filters = list(data.get("filters"))
    for filter_obj_str in filters:
        filter_obj = dict(filter_obj_str)
        type_str = filter_obj["type"]
        filter_str = filter_obj["filter"]
        post_filter = PostFilter(post=post.id, type=type_str, filter=filter_str)
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
    data = request.get_json()

    try:
        account_id = data.get("account_id")
        account = PostAccount.get_account(account_id)
        post_id = data.get("post_id")
        post = Post.get_post(post_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if post.account != account.id:
        return jsonify({"error": "Account not authorized to update this post."}), 400

    image_url = data.get("image_url")
    start_date_str = data.get("start_date")
    end_date_str = data.get("end_date")

    if any(x is None for x in [image_url, start_date_str, end_date_str]):
        return jsonify({"error": "Parameter is missing"}), 400

    post.source = data.get("source")
    post.title = data.get("title")
    post.subtitle = data.get("subtitle")
    post.time_label = data.get("time_label")
    post.post_url = data.get("post_url")
    post.image_url = image_url

    post.start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S')
    post.end_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S')

    filters = list(data.get("filters"))
    post.filters = True if filters else False

    PostFilter.query.filter_by(post=post.id).delete()
    for filter_obj_str in filters:
        filter_obj = dict(filter_obj_str)
        type_str = filter_obj["type"]
        filter_str = filter_obj["filter"]
        post_filter = PostFilter(post=post.id, type=type_str, filter=filter_str)
        sqldb.session.add(post_filter)

    status = PostStatus(post=post.id, status="updated")
    sqldb.session.add(status)
    sqldb.session.commit()

    return jsonify({"post_id": post.id})


@app.route('/portal/account/login', methods=['POST'])
def login():
    email = request.form.get("email")
    encrypted_password = request.form.get("encrypted_password")

    if any(x is None for x in [email, encrypted_password]):
        return jsonify({"error": "Parameter is missing"}), 400

    account = PostAccount.query.filter_by(email=email, encrypted_password=encrypted_password).first()
    if account:
        return jsonify({'account_id': account.id, 'email': account.email})
    else:
        return jsonify({'error': 'Unable to authenticate'})


@app.route('/portal/posts', methods=['GET'])
def get_posts():
    account_id = request.args.get("account_id")
    posts = Post.query.filter_by(account=account_id).all()
    json_arr = []
    for post in posts:
        post_json = {
            'source': post.source,
            'title': post.title,
            'subtitle': post.subtitle,
            'time_label': post.time_label,
            'image_url': post.image_url,
            'post_url': post.post_url,
            'filters': []
        }
        if post.filters:
            filters = PostFilter.query.filter_by(post=post.id).all()
            for obj in filters:

                post_json['filters'].append({'type': obj.type, 'filter': obj.filter})

        status = PostStatus.query.filter_by(post=post.id).order_by(desc(PostStatus.created_at)).first()
        post_json['status'] = status.status

        json_arr.append(post_json)
    
    return jsonify({'posts': json_arr})
