from flask import request, jsonify, redirect
from server import app, sqldb, bcrypt
from ..models import PostAccount, Post, PostTester, PostAccountEmail
from sqlalchemy import desc, or_, case, exists, func, and_
from sqlalchemy.sql import select
import json
from datetime import date, datetime, timedelta


@app.route('/portal/account/new', methods=['POST'])
def create_account():
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    encrypted_password = bcrypt.generate_password_hash(password)

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
    password = request.form.get("password")

    if any(x is None for x in [email, password]):
        return jsonify({"error": "Parameter is missing"}), 400

    pw_hash = bcrypt.generate_password_hash(password)
    account = PostAccount.query.filter(PostAccount.email == email and bcrypt.check_password_hash(pw_hash, password)).first()
    if account:
        account.sign_in_count = account.sign_in_count + 1
        account.last_sign_in_at = datetime.now()
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
        return jsonify({'error': 'Account not found.'}), 400

    # TODO: send verification email
    token = str(uuid.uuid4())
    print(token)
    account.reset_password_token = token
    account.reset_password_token_sent_at = datetime.now()
    sqldb.session.commit()
    return jsonify({'msg': 'An email has been sent to reset your password.'})


# Verify a reset password token
@app.route('/portal/account/reset', methods=['GET'])
def verify_account_password_reset():
    token = request.args.get("token")
    now = datetime.now()
    account = PostAccount.query.filter_by(reset_password_token=token).first()
    if not account:
        return jsonify({'error': 'Invalid auth token. Please try again.'})
    elif account.reset_password_token_sent_at and account.reset_password_token_sent_at + timedelta(minutes=30) < now:
        return jsonify({'error': 'This token has expired.'})
    else:
        return redirect("https://pennlabs.org?token={}".format(token), code=302)


# Reset password
@app.route('/portal/account/reset', methods=['POST'])
def reset_account_password():
    token = request.form.get("token")
    password = request.form.get("password")
    encrypted_password = bcrypt.generate_password_hash(password)
    account = PostAccount.query.filter_by(reset_password_token=token).first()
    if not account:
        return jsonify({'error': 'Invalid auth token. Please try again.'})
    elif not encrypted_password:
        return jsonify({'error': 'Invalid password. Please try again.'})

    account.encrypted_password = encrypted_password
    account.updated_at = datetime.now()
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
        now = datetime.now()
        upcoming_posts = Post.query.filter(Post.account == account_email.account).filter(Post.end_date >= now).all()
        for post in upcoming_posts:
            tester = PostTester(post=post.id, email=account_email.email)
            sqldb.session.add(tester)
        sqldb.session.commit()
        return redirect("https://pennlabs.org", code=302)
