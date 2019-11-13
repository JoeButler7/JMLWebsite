import os
import secrets

import flask
from authy.api import AuthyApiClient
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, logout_user, login_required, login_manager


from Site import app, db
from Site.forms import RegForm, LoginForm, UpdateProfileForm, NewPostForm, TokenVerificationForm, PhoneVerificationForm, \
    TokenPhoneValidationForm
from Site.models import User

from .db import db_session
from .decorators import auth_required

authy_api = AuthyApiClient(app.config.get('ACCOUNT_SECURITY_API_KEY'))


@app.route('/')
@app.route('/home')
def home():
    return render_template('app_home.html')


'''
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegForm()
    if form.validate_on_submit():
        hashed_password = argon2.hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account successfully created')
        return redirect(url_for('login'))
    return flask.render_template('create_account.html', form=form)
    '''


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegForm()
    if form.validate_on_submit():
        #!hashed_password = argon2.hash(form.password.data)
        authy_user = authy_api.users.create(
            form.email.data,
            form.phone_number.data,
            form.country_code.data,
        )
        if authy_user.ok():
            user = User(
                form.username.data,
                form.email.data,
               #! hashed_password,
                form.password.data,
                authy_user.id,
                is_authenticated=True
            )
            user.authy_id = authy_user.id
            db_session.add(user)
            db_session.commit()
            login_user(user, remember=True)
            return flask.redirect('/myaccount')
        else:
            form.errors['non_field'] = []
            for key, value in authy_user.errors():
                form.errors['non_field'].append(
                    None,
                    '{key}: {value}'.format(key=key, value=value)
                )
    return flask.render_template('create_account.html', form=form)


@app.route('/auth', methods=['GET', 'POST'])
@login_required
def auth():
    form = TokenVerificationForm(current_user.authy_id)
    if form.validate_on_submit():
        flask.session['authy'] = True
        return flask.redirect('/myaccount')
    return flask.render_template('twofactor_auth.html', form=form)


'''
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and argon2.verify(form.password.data, user.password):
            login_user(user, remember=form.rememberme.data)
            back_page = request.args.get('next')
            if back_page:
                return redirect(back_page)
            else:
                return redirect(url_for('home'))
        else:
            flash('Invalid Email or Password')
        return render_template('login.html', form=form)
    return render_template('login.html', title='Login', form=form)
'''


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        login_user(form.user, remember=True)
        form.user.is_authenticated = True
        db_session.add(form.user)
        db_session.commit()
        next = request.args.get('next')
        return redirect(next or url_for('account'))
    return render_template('login.html', form=form)


@app.route("/logout", methods=["GET"])
@login_required
def logout():
    current_user.is_authenticated = False
    db_session.add(current_user)
    db_session.commit()
    flask.session['authy'] = False
    flask.session['is_verified'] = False
    logout_user()
    logout_user()
    return redirect(url_for('home'))


@app.route('/myaccount')
@login_required
@auth_required
def account():
    profile_pic = url_for('static', filename='profilepics/' + current_user.profile_pic)
    return render_template('myaccount.html', title='Account', profile_pic=profile_pic)


def saveimg(img):
    newname = secrets.token_hex(5)
    _, ext = os.path.splitext(img.filename)
    fn = newname + ext
    img_path = os.path.join(app.root_path, 'static/profile_pics', fn)
    img.save(img_path)
    return fn


@app.route('/updateaccount', methods=['GET', 'POST'])
@login_required
def updateaccount():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        if form.picture.data:
            profile_pic = saveimg(form.picture.data)
            current_user.profile_pic = profile_pic
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit
        flash('Account successfully updated')
        return redirect(url_for('account'))
    profile_pic = url_for('static', filename='profilepics/' + current_user.profile_pic)
    return render_template('update.html', title='Update Profile', profile_pic=profile_pic, form=form)


@app.route('/newpost', methods=['POST', 'GET'])
@login_required
def newpost():
    form = NewPostForm()
    if form.validate_on_submit:
        newpost = Post(Title=form.title.data, Category=form.type.data, content=form.contend.data,
                       author_id=current_user)
        db.session.add(newpost)
        db.session.commit
        flash("Successfully Posted")
        return redirect(url_for('home'))
    return render_template('newpost.html', title='New Post', form=form)


######################
# TOKEN VERIFICATION #
######################


@app.route('/token/sms', methods=['POST'])
@login_required
def token_sms():
    sms = authy_api.users.request_sms(current_user.authy_id, {'force': True})
    if sms.ok():
        return flask.Response('SMS request successful', status=200)
    else:
        return flask.Response('SMS request failed', status=503)


@app.route('/token/voice', methods=['POST'])
@login_required
def token_voice():
    call = authy_api.users.request_call(current_user.authy_id, {'force': True})
    if call.ok():
        return flask.Response('Call request successful', status=200)
    else:
        return flask.Response('Call request failed', status=503)


@app.route('/token/onetouch', methods=['POST'])
@login_required
def token_onetouch():
    details = {
        'Authy ID': current_user.authy_id,
        'Username': current_user.username,
        'Reason': 'Demo by Account Security'
    }

    hidden_details = {
        'test': 'This is a'
    }

    response = authy_api.one_touch.send_request(
        int(current_user.authy_id),
        message='Login requested for Account Security account.',
        seconds_to_expire=120,
        details=details,
        hidden_details=hidden_details
    )
    if response.ok():
        flask.session['onetouch_uuid'] = response.get_uuid()
        return flask.Response('OneTouch request successfull', status=200)
    else:
        return flask.Response('OneTouch request failed', status=503)


@app.route('/onetouch-status', methods=['POST'])
@login_required
def onetouch_status():
    uuid = flask.session['onetouch_uuid']
    approval_status = authy_api.one_touch.get_approval_status(uuid)
    if approval_status.ok():
        if approval_status['approval_request']['status'] == 'approved':
            flask.session['authy'] = True
        return flask.Response(
            approval_status['approval_request']['status'],
            status=200
        )
    else:
        return flask.Response(approval_status.errros(), status=503)


######################
# Phone Verification #
######################

@app.route('/verification', methods=['GET', 'POST'])
def phone_verification():
    form = PhoneVerificationForm()
    if form.validate_on_submit():
        flask.session['phone_number'] = form.phone_number.data
        flask.session['country_code'] = form.country_code.data
        authy_api.phones.verification_start(
            form.phone_number.data,
            form.country_code.data,
            via=form.via.data
        )
        return flask.redirect('/verification/token')
    return flask.render_template('phone_verification.html', form=form)


@app.route('/verification/token', methods=['GET', 'POST'])
def token_validation():
    form = TokenPhoneValidationForm()
    if form.validate_on_submit():
        verification = authy_api.phones.verification_check(
            flask.session['phone_number'],
            flask.session['country_code'],
            form.token.data
        )
        if verification.ok():
            flask.session['is_verified'] = True
            return flask.redirect('/verified')
        else:
            form.errors['non_field'] = []
            for error_msg in verification.errors().values():
                form.errors['non_field'].append(error_msg)
    return flask.render_template('token_validation.html', form=form)


@app.route('/verified')
def verified():
    if not flask.session.get('is_verified'):
        return flask.redirect('/verification')
    return flask.render_template('authenticated_user.html')
