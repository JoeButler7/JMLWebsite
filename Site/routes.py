import os
import secrets
import datetime

import flask
from flask_socketio import SocketIO
from authy.api import AuthyApiClient
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, logout_user, login_required, login_manager
from passlib.hash import argon2
from Site import app, db, mail
from Site.forms import RegForm, LoginForm, UpdateProfileForm, NewPostForm, TokenVerificationForm, PhoneVerificationForm, \
    TokenPhoneValidationForm, ResetPassFrom, ResetPassRequestForm
from Site.models import User, Post
from flask_mail import Message
from .db import db_session
from .decorators import auth_required
from pprint import pprint

authy_api = AuthyApiClient(app.config.get('ACCOUNT_SECURITY_API_KEY'))

socketio = SocketIO(app)


@app.route('/')
@app.route('/home')
def home():
    return render_template('app_home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegForm()
    if form.validate_on_submit():
        authy_user = authy_api.users.create(
            form.email.data,
            form.phone_number.data,
            form.country_code.data,
        )
        if authy_user.ok():
            user = User(
                form.username.data,
                form.email.data,
                form.password.data,
                authy_user.id,
                form.country_code.data + form.phone_number.data,
                is_authenticated=True
            )
            user.authy_id = authy_user.id
            db_session.add(user)
            db_session.commit()
            login_user(user, remember=True)
            send_confirm_email(user)
            return flask.redirect('/auth')
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
@auth_required
def account():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    profile_pic = url_for('static', filename='profilepics/' + current_user.profile_pic)
    return render_template('myaccount.html', title='Account', profile_pic=profile_pic, user=current_user)


def saveimg(img):
    newname = secrets.token_hex(5)
    _, ext = os.path.splitext(img.filename)
    fn = newname + ext
    img_path = os.path.join(app.root_path, 'static/profilepics', fn)
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
        if form.username.data:
            current_user.username = form.username.data
        if form.email.data:
            current_user.email = form.email.data
            current_user.email_verified = False
        db_session.commit()
        if form.email.data:
            send_confirm_email(current_user)
        flash('Account successfully updated')
        login_user(current_user, remember=False)
        return redirect(url_for('account'))
    profile_pic = url_for('static', filename='profilepics/' + current_user.profile_pic)
    return render_template('update.html', title='Update Profile', profile_pic=profile_pic, form=form, user=current_user)


@app.route('/users/<username>')
def useraccounts(username):
    user = User.load_user(username)
    if user is None:
        flash('Invalid User')
        return redirect(url_for('account'))
    if current_user.is_authenticated:
        if user.username == current_user.username:
            return redirect(url_for('account'))
    profile_pic = url_for('static', filename='profilepics/' + user.profile_pic)
    return render_template('useraccount.html', title=username, profile_pic=profile_pic, user=user)


@app.route('/users/<username>/follow')
@login_required
def follow(username):
    user = User.load_user(username)
    if user is None:
        flash('Invalid User')
        return redirect(url_for('account'))
    if current_user.is_following(user):
        flash('You are already following %s' % username)
        return redirect(url_for('useraccounts', username=username))
    current_user.follow(user)
    db_session.commit()
    flash('You are now following %s' % username)
    return redirect(url_for('useraccounts', username=username))


@app.route('/users/<username>/unfollow')
@login_required
def unfollow(username):
    user = User.load_user(username)
    if user is None:
        flash('Invalid User')
        return redirect(url_for('account'))
    if not current_user.is_following(user):
        flash('You not following %s' % username)
        return redirect(url_for('useraccounts', username=username))
    current_user.unfollow(user)
    db_session.commit()
    return redirect(url_for('useraccounts', username=username))


######################
# Posts #
######################

@app.route('/posts/create', methods=['GET', 'POST'])
def newpost():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    form = NewPostForm()

    if form.validate_on_submit():
        post = Post(Title=form.title.data, content=form.content.data, Category=form.type.data, name=form.name.data,
                    rating=form.rating.data)
        db_session.add(post)
        db_session.commit()
        flash("Successfully Posted")
        return redirect(url_for('home'))
    app.logger.debug(form.errors)
    return render_template('newpost.html', title='New Post', form=form)


@app.route('/posts/all')
def allPosts():
    posts = Post.query.all()
    return render_template("post_feed.html", posts=posts)


@app.route('/posts/myposts')
def myPosts():
    users = User.query.all()
    return render_template("mypost_feed.html", users=users)


@app.route('/posts/bars')
def barPosts():
    posts = Post.query.all()
    return render_template("post_bars_feed.html", posts=posts)


@app.route('/posts/restaurants')
def restaurantsPosts():
    posts = Post.query.all()
    return render_template("post_restaurants_feed.html", posts=posts)


@app.route('/posts/entertainment')
def entertainmentPosts():
    posts = Post.query.all()
    return render_template("post_entertainment_feed.html", posts=posts)


@app.route('/posts/services')
def servicesPosts():
    posts = Post.query.all()
    return render_template("post_services_feed.html", posts=posts)


@app.route('/posts/libraries')
def librariesPosts():
    posts = Post.query.all()
    return render_template("post_libraries_feed.html", posts=posts)


@app.route('/posts/dining')
def diningPosts():
    posts = Post.query.all()
    return render_template("post_dining_feed.html", posts=posts)


@app.route('/posts/bathrooms')
def bathroomPosts():
    posts = Post.query.all()
    return render_template("post_bathrooms_feed.html", posts=posts)


@app.route('/posts/programs')
def programsPosts():
    posts = Post.query.all()
    return render_template("post_program_feed.html", posts=posts)


@app.route('/posts/professors')
def professorsPosts():
    posts = Post.query.all()
    return render_template("post_professor_feed.html", posts=posts)


@app.route('/posts/studyspot')
def studyspotPosts():
    posts = Post.query.all()
    return render_template("post_studyspot_feed.html", posts=posts)


@app.route('/posts/class')
def classPosts():
    posts = Post.query.all()
    return render_template("post_class_feed.html", posts=posts)


@app.route('/like/<int:post_id>/<action>')
@login_required
def like_action(post_id, action):
    post = Post.query.filter_by(id=post_id).first()
    #print(post_id)
   # print(post)
    if action == 'like':
        current_user.like_post(post)
        db_session.commit()
    if action == 'unlike':
        current_user.unlike_post(post)
        db_session.commit()
    return redirect(request.referrer)


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


####################
# Email Confirmation#
####################
def send_confirm_email(user):
    token = user.get_confirm_token()
    msg = Message('Confirm Your Email', sender='noreply@overRated.com',
                  recipients=user.email.split())
    msg.body = f'''To confirm your password, click the following link
{url_for('confirm_email', token=token, _external=True)}

If you did not register for an overRated account ignore this email
'''
    mail.send(msg)


@app.route('/confirm_email/<username>', methods=['POST', 'GET'])
@login_required
def confirm_request(username):
    user = User.load_user(username)
    if user:
        send_confirm_email(user)
        flash('A confirmation reset email has been sent')
    return redirect(url_for('account'))


@app.route('/confirm/<token>', methods=['POST', 'GET'])
def confirm_email(token):
    user = User.verify_confrim_token(token)
    if user is None:
        flash('Invalid or expired token', 'warning')
        return redirect(url_for('account'))
    user.email_verified = True
    db_session.commit()
    return render_template('confirmed.html')


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


#############
# Live Chat #
#############
@app.route('/chat')
@login_required
def sessions():
    return render_template('chat.html', user=current_user)


def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')


@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('received my event: ' + str(json))
    socketio.emit('my response', json, callback=messageReceived)


##################
# Password Reset #
##################
def send_reset_email(user):
    token = user.get_confirm_token()
    msg = Message('Password Reset', sender='noreply@overRated.com',
                  recipients=user.email.split())
    msg.body = f'''To reset your password, click the following link
{url_for('reset_password', token=token, _external=True)}

If you did not request a password reset ignore this email
'''
    mail.send(msg)


@app.route('/resetrequest', methods=['POST', 'GET'])
def resetrequest():
    form = ResetPassRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('A Password reset email has been sent')
        return redirect(url_for('login'))
    return render_template('Reset_request.html', title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['POST', 'GET'])
def reset_password(token):
    user = User.verify_confrim_token(token)
    if user is None:
        flash('Invalid or expired token', 'warning')
        return redirect(url_for('resetrequest'))
    form = ResetPassFrom()
    if form.validate_on_submit():
        print('Valid')
        user.pw_hash = argon2.hash(form.password.data)
        db_session.commit()
        flash('Password updated')
        return redirect(url_for('login'))
    return render_template('reset_password.html', title='Reset Password', form=form)


if __name__ == '__main__':
    socketio.run(app, debug=True)
