from flask import render_template, redirect, url_for, request,flash, request
from flask_login import login_user, current_user, logout_user, login_required
from passlib.hash import argon2
from Site import app, db
from Site.Forms import RegFrom, LoginForm, UpdateProfileForm
from Site.models import User, Post






@app.route('/')
@app.route('/home')
def home():
    return render_template('app_home.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form=RegFrom()
    if form.validate_on_submit():
        hashed_password=argon2.hash(form.password.data)
        user=User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account successfully created')
        return redirect(url_for('login'))
    return render_template('create_account.html', form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form=LoginForm()
    if form.validate_on_submit():
        user =User.query.filter_by(email=form.email.data).first()
        if user and argon2.verify(form.password.data, user.password):
            login_user(user, remember=form.rememberme.data)
            back_page=request.args.get('next')
            if back_page:
                return redirect(back_page)
            else:
                return redirect(url_for('home'))
        else:
            flash('Invalid Email or Password')
        return render_template('login.html', form=form)
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/myaccount')
@login_required
def account():
    profile_pic=url_for('static', filename='profilepics/'+current_user.profile_pic)
    return render_template('myaccount.html',profile_pic=profile_pic)


@app.route('/updateaccount', methods=['GET', 'POST'])
@login_required
def updateaccount():
    form=UpdateProfileForm()
    if form.validate_on_submit():
        current_user.username=form.username.data
        current_user.email=form.email.data
        db.session.commit
        flash('Account successfully updated')
        return redirect(url_for('account'))
    profile_pic=url_for('static', filename='profilepics/'+current_user.profile_pic)
    return render_template('update.html',profile_pic=profile_pic,form=form)
