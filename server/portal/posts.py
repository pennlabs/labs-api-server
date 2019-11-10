from datetime import datetime

from flask import jsonify, request
from sqlalchemy import and_, desc, func

from server import app, sqldb
from server.models import (AnalyticsEvent, Post, PostFilter, PostStatus,
                           PostTargetEmail, PostTester, School, SchoolMajorAccount)


"""
Endpoint: /portal/posts
HTTP Methods: GET
Response Formats: JSON
Parameters: account

Returns list of posts
"""
@app.route('/portal/posts', methods=['GET'])
def get_posts():
    account_id = request.args.get('account')
    posts = Post.query.filter_by(account=account_id).all()
    posts_query = sqldb.session.query(Post.id).filter_by(account=account_id).subquery()

    qry1 = sqldb.session.query(AnalyticsEvent.post_id.label('id'),
                               func.count(AnalyticsEvent.post_id).label('interactions')) \
                        .filter(AnalyticsEvent.type == 'post') \
                        .filter(AnalyticsEvent.post_id.in_(posts_query)) \
                        .filter(AnalyticsEvent.is_interaction) \
                        .group_by(AnalyticsEvent.post_id) \
                        .subquery()

    qry2 = sqldb.session.query(AnalyticsEvent.post_id.label('id'),
                               func.count(AnalyticsEvent.post_id).label('impressions')) \
                        .filter(AnalyticsEvent.type == 'post') \
                        .filter(AnalyticsEvent.post_id.in_(posts_query)) \
                        .filter(AnalyticsEvent.is_interaction == 0) \
                        .group_by(AnalyticsEvent.post_id) \
                        .subquery()

    qry3_sub = sqldb.session.query(AnalyticsEvent.post_id.label('id'), AnalyticsEvent.user) \
                            .filter(AnalyticsEvent.type == 'post') \
                            .filter(AnalyticsEvent.post_id.in_(posts_query)) \
                            .filter(AnalyticsEvent.is_interaction == 0) \
                            .group_by(AnalyticsEvent.post_id, AnalyticsEvent.user) \
                            .subquery()

    qry3 = sqldb.session.query(qry3_sub.c.id, func.count(qry3_sub.c.user).label('unique_impr')) \
                        .select_from(qry3_sub) \
                        .group_by(qry3_sub.c.id) \
                        .subquery()

    analytics_qry = sqldb.session.query(qry1.c.id, qry1.c.interactions, qry2.c.impressions, qry3.c.unique_impr) \
                                .select_from(qry1) \
                                .join(qry2, qry1.c.id == qry2.c.id) \
                                .join(qry3, and_(qry1.c.id == qry2.c.id, qry2.c.id == qry3.c.id)) \
                                .all()

    analytics_by_post = {}
    for post_id, interactions, impressions, unique_impr in analytics_qry:
        analytics_by_post[post_id] = (interactions, impressions, unique_impr)

    json_arr = []
    for post in posts:
        post_json = get_post_json(post)
        if str(post.id) in analytics_by_post:
            (interactions, impressions, unique_impr) = analytics_by_post[str(post.id)]
            post_json['interactions'] = interactions
            post_json['impressions'] = impressions
            post_json['unique_impressions'] = unique_impr
        elif post.approved:
            post_json['interactions'] = 0
            post_json['impressions'] = 0
            post_json['unique_impressions'] = 0
        else:
            post_json['interactions'] = None
            post_json['impressions'] = None
            post_json['unique_impressions'] = None
        json_arr.append(post_json)
    return jsonify({'posts': json_arr})


"""
Endpoint: /portal/posts/<post_id>
HTTP Methods: GET
Response Formats: JSON
Parameters: account

Returns post information by post ID for an account
"""
@app.route('/portal/post/<int:post_id>', methods=['GET'])
def get_post(post_id):
    account_id = request.args.get('account')
    post = Post.query.filter_by(id=post_id, account=account_id).first()
    if not post:
        return jsonify({'error': 'Post not found.'}), 400

    post_json = get_post_json(post)
    return jsonify(post_json)


def get_post_json(post):
    post_json = {
        'id': post.id,
        'source': post.source,
        'title': post.title,
        'subtitle': post.subtitle,
        'time_label': post.time_label,
        'image_url': post.image_url,
        'image_url_cropped': post.image_url_cropped,
        'post_url': post.post_url,
        'start_date': datetime.strftime(post.start_date, '%Y-%m-%dT%H:%M:%S'),
        'end_date': datetime.strftime(post.end_date, '%Y-%m-%dT%H:%M:%S'),
        'filters': [],
        'testers': [],
        'emails': []
    }
    filters = PostFilter.query.filter_by(post=post.id).all()
    for obj in filters:
        post_json['filters'].append({'type': obj.type, 'filter': obj.filter})

    testers = sqldb.session.query(PostTester.email).filter_by(post=post.id).all()
    post_json['testers'] = [x for (x,) in testers]

    emails = sqldb.session.query(PostTargetEmail.email).filter_by(post=post.id).all()
    post_json['emails'] = [x for (x,) in emails]

    status = PostStatus.query.filter_by(post=post.id).order_by(desc(PostStatus.created_at)).first()
    post_json['status'] = status.status
    post_json['comments'] = status.msg
    return post_json


def get_posts_for_account(account):
    now = datetime.now()
    post_arr = []

    if not account:
        posts = Post.query.filter(Post.start_date <= now,
                                  now <= Post.end_date,
                                  Post.filters.is_(False),
                                  Post.approved.is_(True)).all()
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
    now = datetime.now()
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
    now = datetime.now()
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
    now = datetime.now()
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
        'image_url_cropped': post.image_url_cropped,
        'post_url': post.post_url,
        'post_id': post.id,
        'test': test
    }
    return post_json
