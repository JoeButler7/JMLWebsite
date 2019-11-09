from flask import render_template, redirect, url_for, request,flash, request
from flask_login import login_user, current_user, logout_user, login_required
from passlib.hash import argon2
from Site import app, db
from Site.Forms import RegFrom, LoginForm, UpdateProfileForm, NewPostForm
from Site.models import User, Post
import secrets, os






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
    return render_template('login.html',title='Login',form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/myaccount')
@login_required
def account():
    profile_pic=url_for('static', filename='profilepics/'+current_user.profile_pic)
    return render_template('myaccount.html', title='Account', profile_pic=profile_pic)



def saveimg(img):
    newname=secrets.token_hex(5)
    _, ext=os.path.splitext(img.filename)
    fn=newname+ext
    img_path=os.path.join(app.root_path,'static/profile_pics', fn)
    img.save(img_path)
    return fn


@app.route('/updateaccount', methods=['GET', 'POST'])
@login_required
def updateaccount():
    form=UpdateProfileForm()
    if form.validate_on_submit():
        if form.picture.data:
            profile_pic=saveimg(form.picture.data)
            current_user.profile_pic=profile_pic
        current_user.username=form.username.data
        current_user.email=form.email.data
        db.session.commit
        flash('Account successfully updated')
        return redirect(url_for('account'))
    profile_pic=url_for('static', filename='profilepics/'+current_user.profile_pic)
    return render_template('update.html',title='Update Profile',profile_pic=profile_pic,form=form)




@app.route('/newpost', methods=['POST','GET'])
@login_required
def newpost():
    form=NewPostForm()
    if form.validate_on_submit:
        newpost=Post(Title=form.title.data,Category=form.type.data, content=form.contend.data, author_id=current_user)
        db.session.add(newpost)
        db.session.commit
        flash("Successfully Posted")
        return redirect(url_for('home'))
    return render_template('newpost.html', title='New Post', form=form)
