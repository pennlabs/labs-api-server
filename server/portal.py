from flask import request, jsonify, redirect
from server import app, sqldb
from .models import PostAccount, Post, PostFilter, PostStatus, PostTester, PostTargetEmail, SchoolMajorAccount, School, Major
from .models import PostAccountEmail
from sqlalchemy import desc, or_, case, exists
from sqlalchemy.sql import select
import json
import datetime
import uuid


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
    ],
    "testers": [
        "amyg@upenn.edu"
    ],
    "emails": [
        "benfranklin@upenn.edu",
        "elonmusk@upenn.edu"
    ],
    "comments": "This is a post to test Penn Mobile. Please approve!"
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
    testers = list(data.get("testers"))
    emails = list(data.get("emails"))

    start_date_str = data.get("start_date")
    end_date_str = data.get("end_date")

    if any(x is None for x in [image_url, start_date_str, end_date_str]):
        return jsonify({"error": "Parameter is missing"}), 400

    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S')
    end_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S')

    post = Post(account=account.id, source=source, title=title, subtitle=subtitle, time_label=time_label, post_url=post_url,
                image_url=image_url, start_date=start_date, end_date=end_date, filters=(True if filters else False),
                testers=(True if testers else False), emails=(True if emails else False))
    sqldb.session.add(post)
    sqldb.session.commit()

    add_filters_testers_emails(account, post, filters, testers, emails)

    msg = data.get("comments")
    update_status(post, "submitted", msg)

    return jsonify({"post_id": post.id})


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
    testers = list(data.get("testers"))
    emails = list(data.get("emails"))
    post.filters = True if filters else False
    post.testers = True if testers else False
    post.emails = True if emails else False

    PostFilter.query.filter_by(post=post.id).delete()
    PostTester.query.filter_by(post=post.id).delete()
    PostTargetEmail.query.filter_by(post=post.id).delete()

    add_filters_testers_emails(account, post, filters, testers, emails)

    msg = data.get("comments")
    update_status(post, "updated", msg)

    return jsonify({"post_id": post.id})


@app.route('/portal/post/approve', methods=['POST'])
def approve_post():
    try:
        account_id = request.form.get("account_id")
        account = PostAccount.get_account(account_id)
        post_id = request.form.get("post_id")
        post = Post.get_post(post_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Verify that this account is Penn Labs
    if account.email != "pennappslabs@gmail.com":
        return jsonify({"error": "This account does not have permission to issue post approval decisions."}), 400

    approved = bool(account.form.get("approved"))
    if approved:
        post.approved = True
        update_status(post, "approved", None)
    else:
        # TODO: Send rejection email
        post.approved = False
        msg = account.form.get("msg")
        if not msg:
            return jsonify({"error": "Denied posts must include a reason"}), 400
        update_status(post, "rejected", msg)

    return jsonify({"post_id": post.id})


# Adds filters, testers, and emails to post. If tester is not verified, a verification email is sent and added later.
def add_filters_testers_emails(account, post, filters, testers, emails):
    for filter_obj_str in filters:
        filter_obj = dict(filter_obj_str)
        post_filter = PostFilter(post=post.id, type=filter_obj["type"], filter=filter_obj["filter"])
        sqldb.session.add(post_filter)

    verified_testers = sqldb.session.query(PostAccountEmail.email).filter_by(account=account.id, verified=True).all()
    unverified_testers = PostAccountEmail.query.filter_by(account=account.id, verified=False).all()
    for tester in testers:
        if tester in verified_testers:
            post_tester = PostTester(post=post.id, email=tester)
            sqldb.session.add(post_tester)
        else:
            # TODO: send verification email
            token = str(uuid.uuid4())
            if any(tester == x.email for x in unverified_testers):
                unverified_tester = next(x for x in unverified_testers if x.email == tester)
                unverified_tester.auth_token = token
            else:
                account_email = PostAccountEmail(account=account.id, email=tester, auth_token=token)
                sqldb.session.add(account_email)
            print("Email {} with link: localhost:5000/portal/email/verify?token={}".format(tester, token))

    for email in emails:
        post_email = PostTargetEmail(post=post.id, email=email)
        sqldb.session.add(post_email)

    sqldb.session.commit()


def update_status(post, status, msg):
    status = PostStatus(post=post.id, status="updated", msg=msg)
    sqldb.session.add(status)
    sqldb.session.commit()


@app.route('/portal/account/new', methods=['POST'])
def create_account():
    name = request.form.get("name")
    email = request.form.get("email")
    encrypted_password = request.form.get("encrypted_password")

    if any(x is None for x in [name, email, encrypted_password]):
        return jsonify({"error": "Parameter is missing"}), 400

    account_exists = sqldb.session.query(exists().where(PostAccount.email == email)).scalar()
    if account_exists:
        return jsonify({'msg': 'An account already exists for this email.'}), 400

    account = PostAccount(name=name, email=email, encrypted_password=encrypted_password)
    sqldb.session.add(account)
    sqldb.session.commit()
    return jsonify({'account_id': account.id})


# Login and retrieve account ID
@app.route('/portal/account/login', methods=['POST'])
def login():
    email = request.form.get("email")
    encrypted_password = request.form.get("encrypted_password")

    if any(x is None for x in [email, encrypted_password]):
        return jsonify({"error": "Parameter is missing"}), 400

    account = PostAccount.query.filter_by(email=email, encrypted_password=encrypted_password).first()
    if account:
        account.sign_in_count = account.sign_in_count + 1
        account.last_sign_in_at = datetime.datetime.now()
        sqldb.session.commit()
        return jsonify({'account_id': account.id})
    else:
        return jsonify({'error': 'Unable to authenticate'}), 400


# Get all relevant information for an account
@app.route('/portal/account', methods=['GET'])
def get_account_info():
    try:
        account_id = request.args.get("account_id")
        account = PostAccount.get_account(account_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    verified_emails = sqldb.session.query(PostAccountEmail.email).filter_by(account=account.id, verified=True).all()
    account_json = {
        'id': account.id,
        'name': account.name,
        'email': account.email,
        'verified_emails': verified_emails
    }
    return jsonify({'account': account_json})


# Request password reset
@app.route('/portal/account/reset/request', methods=['POST'])
def request_account_password_reset_token():
    email = request.form.get("email")
    account = PostAccount.query.filter_by(email=email).first()
    if not account:
        return jsonify({'error': 'Account not found with this email'}), 400

    # TODO: send verification email
    token = str(uuid.uuid4())
    account.reset_password_token = token
    account.reset_password_token_sent_at = datetime.datetime.now()
    sqldb.session.commit()
    return jsonify({'msg': 'An email has been sent to reset your password.'})


# Verify a reset password token
@app.route('/portal/account/reset', methods=['GET'])
def verify_account_password_reset():
    token = request.args.get("token")
    now = datetime.datetime.now()
    account = PostAccount.query.filter_by(reset_password_token=token).first()
    if not account:
        return jsonify({'error': 'Invalid auth token. Please try again.'})
    elif account.reset_password_token_sent_at and account.reset_password_token_sent_at.time_delta(minutes=30) < now:
        return jsonify({'error': 'This token has expired.'})
    else:
        return redirect("https://pennlabs.org?token={}".format(token), code=302)


# Reset password
@app.route('/portal/account/reset', methods=['POST'])
def reset_account_password():
    token = request.args.get("token")
    encrypted_password = request.args.get("encrypted_password")
    account = PostAccount.query.filter_by(reset_password_token=token).first()
    if not account:
        return jsonify({'error': 'Invalid auth token. Please try again.'})
    elif not encrypted_password:
        return jsonify({'error': 'Invalid password. Please try again.'})

    account.encrypted_password = encrypted_password
    account.updated_at = datetime.datetime.now()
    sqldb.session.commit()
    return jsonify({'msg': 'Your password has been reset.'})


# Verifies a test email for an account and adds that test email to all upcoming posts
@app.route('/portal/email/verify', methods=['GET'])
def verify_account_email_token():
    token = request.args.get("token")
    account_email = PostAccountEmail.query.filter_by(auth_token=token).first()
    if not account_email:
        return jsonify({'error': 'Invalid auth token. Please try again.'})
    elif account_email.verified:
        return jsonify({'error': 'This email has already been verified for this account.'})
    else:
        account_email.verified = True
        now = datetime.datetime.now()
        upcoming_posts = Post.query.filter(Post.account == account_email.account).filter(Post.end_date >= now).all()
        for post in upcoming_posts:
            tester = PostTester(post=post.id, email=account_email.email)
            sqldb.session.add(tester)
        sqldb.session.commit()
        return redirect("https://pennlabs.org", code=302)


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
            'start_date': datetime.datetime.strftime(post.start_date, '%Y-%m-%dT%H:%M:%S'),
            'end_date': datetime.datetime.strftime(post.end_date, '%Y-%m-%dT%H:%M:%S'),
            'filters': [],
            'testers': [],
            'emails': []
        }
        filters = PostFilter.query.filter_by(post=post.id).all()
        for obj in filters:
            post_json['filters'].append({'type': obj.type, 'filter': obj.filter})

        testers = sqldb.session.query(PostTester.email).filter_by(post=post.id).all()
        post_json['testers'] = testers

        emails = sqldb.session.query(PostTargetEmail.email).filter_by(post=post.id).all()
        post_json['emails'] = emails

        status = PostStatus.query.filter_by(post=post.id).order_by(desc(PostStatus.created_at)).first()
        post_json['status'] = status.status
        post_json['comments'] = status.msg

        json_arr.append(post_json)

    return jsonify({'posts': json_arr})


@app.route('/portal/post/<int:post_id>', methods=['GET'])
def get_post():
    account_id = request.args.get("account")
    post = Post.query.filter_by(id=post_id, account=account_id).first()
    if not post:
        return jsonify({'error': 'Post not found.'}), 400

    post_json = {
        'source': post.source,
        'title': post.title,
        'subtitle': post.subtitle,
        'time_label': post.time_label,
        'image_url': post.image_url,
        'post_url': post.post_url,
        'start_date': datetime.datetime.strftime(post.start_date, '%Y-%m-%dT%H:%M:%S'),
        'end_date': datetime.datetime.strftime(post.end_date, '%Y-%m-%dT%H:%M:%S'),
        'filters': [],
        'testers': [],
        'emails': []
    }
    filters = PostFilter.query.filter_by(post=post.id).all()
    for obj in filters:
        post_json['filters'].append({'type': obj.type, 'filter': obj.filter})

    testers = sqldb.session.query(PostTester.email).filter_by(post=post.id).all()
    post_json['testers'] = testers

    emails = sqldb.session.query(PostTargetEmail.email).filter_by(post=post.id).all()
    post_json['emails'] = emails

    status = PostStatus.query.filter_by(post=post.id).order_by(desc(PostStatus.created_at)).first()
    post_json['status'] = status.status
    post_json['comments'] = status.msg

    return jsonify(post_json)


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

    approved_posts = []
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
