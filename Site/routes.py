from flask import render_template, redirect, url_for, request,flash
from flask_login import login_user
from passlib.hash import sha256_crypt as sha256
from Site import app, db
from Site.Forms import RegFrom, LoginForm
from Site.models import User, Post






@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET','POST'])
def register():
    form=RegFrom()
    if form.validate_on_submit():
        hashed_password=sha256.hash(form.password.data)
        user=User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account successfully created')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        user =User.query.filter_by(email=form.email.data).first()
        if user and sha256.verify(form.password.data, user.password):
            login_user(user, remember=form.rememberme.data)
            return redirect(url_for('home'))
        flash('Invalid Email or Password')
    return render_template('login.html', form=form)
