from flask import request, jsonify
from server import app, sqldb
from .models import PostAccount, Post, PostFilter, PostStatus, PostTester, PostTargetEmail, SchoolMajorAccount, School, Major
from sqlalchemy import desc, or_, case
from sqlalchemy.sql import select
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
    post.end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M:%S')

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


@app.route('/portal/filters', methods=['GET'])
def get_filters():
    filters_by_type = {}
    filters_by_type['email-only'] = {'name': 'Email-Filtering Only', 'filter': 'none'}
    filters_by_type['school'] = [
        {'name': 'Wharton Undegraduate (WH)', 'filter': 'WH'},
        {'name': 'College of Arts & Sciences (SAS)', 'filter': 'COL'},
        {'name': 'Engineering & Applied Science (SEAS)', 'filter': 'EAS'},
        {'name': 'Nursing Undegraduate (NURS)', 'filter': 'NURS'}
    ]

    today = datetime.date.today()
    senior_class_year = today.year
    if today.month >= 6:
        # If after May, current senior class will graduate in following year
        senior_class_year = senior_class_year + 1

    class_filters = []
    for i in range(4):
        name = 'Class of {}'.format(senior_class_year + i)
        filter = str(senior_class_year + i)
        class_filters.append({'name': name, 'filter': filter})
    filters_by_type['class'] = class_filters

    major_filters = []
    majors = Major.query.all()
    for major in majors:
        major_filters.append({'name': major.name, 'filter': major.code})
    filters_by_type['major'] = major_filters

    return jsonify({'filters_by_type': filters_by_type})


def get_posts_for_account(account):
    now = datetime.datetime.now()
    post_arr = []

    if not account:
        posts = Post.query.filter(Post.start_date <= now, now <= Post.end_date, Post.filters.is_(False), Post.approved.is_(True)).all()
        for post in posts:
            post_json = get_json_for_post(post, False)
            post_arr.append(post_json)
    else:
        tester_posts = get_posts_where_tester(account)
        email_posts = get_email_targeted_posts(account)
        filtered_posts = get_filtered_posts(account)

        post_arr.extend(tester_posts)
        filtered_posts.extend(email_posts)
        for post in filtered_posts:
            if not any(post['post_id'] == post_obj['post_id'] for post_obj in post_arr):
                post_arr.append(post)
    return post_arr


def get_posts_where_tester(account):
    # Find any posts that have yet to end for which this account is a tester
    now = datetime.datetime.now()
    post_testers = sqldb.session.query(Post) \
                                .join(PostTester, isouter=True, full=False) \
                                .filter(Post.end_date >= now) \
                                .filter(Post.testers.is_(True)) \
                                .filter(PostTester.email.contains(account.pennkey)) \
                                .all()
    # Add test posts 
    post_arr = [] 
    for post in post_testers:
        post_json = get_json_for_post(post, True)
        post_arr.append(post_json)
    return post_arr


def get_email_targeted_posts(account):
    # Find running posts that have yet to end for which this account is in target email list 
    now = datetime.datetime.now() 
    posts_emails = sqldb.session.query(Post) \
                                .join(PostTargetEmail, isouter=True, full=False) \
                                .filter(Post.start_date <= now) \
                                .filter(Post.end_date >= now) \
                                .filter(Post.emails.is_(True)) \
                                .filter(Post.approved.is_(True)) \
                                .filter(PostTargetEmail.email.contains(account.pennkey)) \
                                .all()
    # Add email targeted posts
    post_arr = [] 
    for post in posts_emails:
        post_json = get_json_for_post(post, False)
        post_arr.append(post_json)
    return post_arr


def get_filtered_posts(account):
    now = datetime.datetime.now()
    majr_filters = sqldb.session.query(SchoolMajorAccount.major, SchoolMajorAccount.expected_grad, School.code) \
                                .join(School, School.id == SchoolMajorAccount.school_id) \
                                .filter(SchoolMajorAccount.account_id == account.id) \
                                .all()

    grad_years = set()
    school_codes = set()
    majors = set()
    for (major, grad, code) in majr_filters:
        school_codes.add(code)
        majors.add(major)

        # If grad is Fall 2019, round up grad year to 2020
        grad_years_list = [int(s) for s in grad.split() if s.isdigit()]
        if grad_years_list:
            year = grad_years_list[0]
            if 'Fall' in grad:
                year = year + 1
            grad_years.add(year)

    post_filters = sqldb.session.query(Post, PostFilter) \
                                .join(PostFilter, isouter=True, full=False) \
                                .filter(Post.start_date <= now) \
                                .filter(Post.end_date >= now) \
                                .filter(Post.approved.is_(True)) \
                                .all()

    approved_posts=[]
    post_filter_dict = {}
    for (post, filter_obj) in post_filters:
        if filter_obj.type == 'email-only' and filter_obj.filter == 'none':
            continue

        if post.id not in post_filter_dict:
            approved_posts.append(post)
            if filter_obj:
                post_filter_dict[post.id] = {filter_obj}
            else:
                post_filter_dict[post.id] = set()
        else:
            post_filter_dict[post.id].add(filter_obj)

    post_arr = []
    for post in approved_posts:
        filters = post_filter_dict[post.id]
        filters_by_type = {}
        for filter_obj in filters:
            if filter_obj.type in filters_by_type:
                filters_by_type[filter_obj.type].add(filter_obj.filter)
            else:
                filters_by_type[filter_obj.type] = {filter_obj.filter}

        # Class Year
        if 'class' in filters_by_type:
            class_filters = filters_by_type['class']
            if not any(int(x) in grad_years for x in class_filters):
                # Reject post if no class filters match a grad year
                continue

        # School
        if 'school' in filters_by_type:
            school_filters = filters_by_type['school']
            if not any(x in school_codes for x in school_filters):
                # Reject post if no class filters match a grad year
                continue

        # Major
        if 'major' in filters_by_type:
            major_filters = filters_by_type['major']
            if not any(x in majors for x in major_filters):
                # Reject post if no class filters match a grad year
                continue

        # Accept post if passes all conditions (not a test post)
        post_json = get_json_for_post(post, False)
        post_arr.append(post_json)
    return post_arr


def get_json_for_post(post, test):
    post_json = {
        'source': post.source,
        'title': post.title,
        'subtitle': post.subtitle,
        'time_label': post.time_label,
        'image_url': post.image_url,
        'post_url': post.post_url,
        'post_id': post.id,
        'test': test
    }
    return post_json
