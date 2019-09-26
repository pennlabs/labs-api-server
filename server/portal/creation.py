import json
import os
import sys
import uuid
from datetime import date, datetime, timedelta

import tinify
from flask import jsonify, redirect, request
from sqlalchemy import and_, case, desc, exists, func, or_
from sqlalchemy.sql import select

from server import app, bcrypt, s3, sqldb
from server.models import (Major, Post, PostAccount, PostAccountEmail,
                           PostFilter, PostStatus, PostTargetEmail, PostTester)


"""
Example: JSON Encoding
{
    'account_id': '7900fffd-0223-4381-a61d-9a16a24ca4b7',
    'image_url': 'https://i.imgur.com/CmhAG25.jpg',
    'post_url': 'https://pennlabs.org/',
    'source': 'Penn Labs',
    'subtitle': 'A small subtitle',
    'time_label': 'Today',
    'title': 'Testing a new feature!',
    'start_date': '2019-05-23T08:00:00',
    'end_date': '2019-05-24T00:00:00',
    'filters': [
        {
            'type': 'class',
            'filter': '2020'
        },
        {
            'type': 'class',
            'filter': '2021'
        },
        {
            'type': 'major',
            'filter': 'CIS'
        }
    ],
    'testers': [
        'amyg@upenn.edu'
    ],
    'emails': [
        'benfranklin@upenn.edu',
        'elonmusk@upenn.edu'
    ],
    'comments': 'This is a post to test Penn Mobile. Please approve!'
}
"""


@app.route('/portal/post/new', methods=['POST'])
def create_post():
    data = request.get_json()

    try:
        account_id = data.get('account_id')
        account = PostAccount.get_account(account_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    source = data.get('source')
    title = data.get('title')
    subtitle = data.get('subtitle')
    time_label = data.get('time_label')
    post_url = data.get('post_url')
    image_url = data.get('image_url')
    filters = list(data.get('filters'))
    testers = list(data.get('testers'))
    emails = list(data.get('emails'))

    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')

    if any(x is None for x in [image_url, start_date_str, end_date_str]):
        return jsonify({'error': 'Parameter is missing'}), 400

    start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M:%S')

    post = Post(account=account.id, source=source, title=title, subtitle=subtitle, time_label=time_label,
                post_url=post_url, image_url=image_url, start_date=start_date, end_date=end_date,
                filters=(True if filters else False), testers=(True if testers else False),
                emails=(True if emails else False)
                )
    sqldb.session.add(post)
    sqldb.session.commit()

    add_filters_testers_emails(account, post, filters, testers, emails)

    msg = data.get('comments')
    update_status(post, 'submitted', msg)

    return jsonify({'post_id': post.id})


@app.route('/portal/post/update', methods=['POST'])
def update_post():
    data = request.get_json()

    try:
        account_id = data.get('account_id')
        account = PostAccount.get_account(account_id)
        post_id = data.get('post_id')
        post = Post.get_post(post_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    if post.account != account.id:
        return jsonify({'error': 'Account not authorized to update this post.'}), 400

    image_url = data.get('image_url')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')

    if any(x is None for x in [image_url, start_date_str, end_date_str]):
        return jsonify({'error': 'Parameter is missing'}), 400

    post.source = data.get('source')
    post.title = data.get('title')
    post.subtitle = data.get('subtitle')
    post.time_label = data.get('time_label')
    post.post_url = data.get('post_url')
    post.image_url = image_url

    post.start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S')
    post.end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M:%S')

    filters = list(data.get('filters'))
    testers = list(data.get('testers'))
    emails = list(data.get('emails'))
    post.filters = True if filters else False
    post.testers = True if testers else False
    post.emails = True if emails else False

    PostFilter.query.filter_by(post=post.id).delete()
    PostTester.query.filter_by(post=post.id).delete()
    PostTargetEmail.query.filter_by(post=post.id).delete()

    add_filters_testers_emails(account, post, filters, testers, emails)

    msg = data.get('comments')
    update_status(post, 'updated', msg)

    return jsonify({'post_id': post.id})


@app.route('/portal/post/image', methods=['POST'])
def save_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No file passed to server'}), 400

    file = request.files['image']
    if not file.filename:
        return jsonify({'error': 'File must have a filename'}), 400

    # Validate account
    try:
        account_id = request.form.get('account')
        account = PostAccount.get_account(account_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    # if request.args.original:
    #     s3.upload_fileobj(file, 'penn.mobile.portal/images/{}'.format(account.name), file.filename)

    source_data = file.read()
    resized_image = tinify.from_buffer(source_data).resize(method='cover', width=600, height=300)
    aws_url = resized_image.store(
        service='s3',
        aws_access_key_id=os.environ.get('AWS_KEY'),
        aws_secret_access_key=os.environ.get('AWS_SECRET'),
        region='us-east-1',
        path='penn.mobile.portal/images/{}/{}'.format(account.name, file.filename)
    ).location

    return jsonify({'image_url': aws_url})


@app.route('/portal/post/approve', methods=['POST'])
def approve_post():
    try:
        account_id = request.form.get('account_id')
        account = PostAccount.get_account(account_id)
        post_id = request.form.get('post_id')
        post = Post.get_post(post_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    # Verify that this account is Penn Labs
    if account.email != 'pennappslabs@gmail.com':
        return jsonify({'error': 'This account does not have permission to issue post approval decisions.'}), 400

    approved = bool(account.form.get('approved'))
    if approved:
        post.approved = True
        update_status(post, 'approved', None)
    else:
        # TODO: Send rejection email
        post.approved = False
        msg = account.form.get('msg')
        if not msg:
            return jsonify({'error': 'Denied posts must include a reason'}), 400
        update_status(post, 'rejected', msg)

    return jsonify({'post_id': post.id})


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

    today = date.today()
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


# Adds filters, testers, and emails to post. If tester is not verified, a verification email is sent and added later.
def add_filters_testers_emails(account, post, filters, testers, emails):
    for filter_obj_str in filters:
        filter_obj = dict(filter_obj_str)
        post_filter = PostFilter(post=post.id, type=filter_obj['type'], filter=filter_obj['filter'])
        sqldb.session.add(post_filter)

    verified_testers = PostAccountEmail.query.filter_by(account=account.id, verified=True).all()
    unverified_testers = PostAccountEmail.query.filter_by(account=account.id, verified=False).all()
    for tester in testers:
        if any(x.email == tester for x in verified_testers):
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
            # print('Email {} with link: localhost:5000/portal/email/verify?token={}'.format(tester, token))

    for email in emails:
        post_email = PostTargetEmail(post=post.id, email=email)
        sqldb.session.add(post_email)

    sqldb.session.commit()


def update_status(post, status, msg):
    status = PostStatus(post=post.id, status='updated', msg=msg)
    sqldb.session.add(status)
    sqldb.session.commit()
