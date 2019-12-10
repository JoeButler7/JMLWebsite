from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import Model, SQLAlchemy
from passlib.hash import argon2
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, backref
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from Site import app

from .db import Base, db_session

from datetime import datetime
from flask_login import UserMixin
from pprint import pprint


db = SQLAlchemy(app)


class Likers(Base):
    __tablename__ = 'likers'

    liker = Column('liker_id', String(50), ForeignKey('users.username'), primary_key=True)
    liked = Column('liked_id', Integer, ForeignKey('post.id'), primary_key=True)


class Follow(Base):
    __tablename__ = 'Follows'

    follower_name = Column(String(50), ForeignKey('users.username'), primary_key=True)
    followed_name = Column(String(50), ForeignKey('users.username'), primary_key=True)


class PostLike(Base,  Model):
    __tablename__ = 'post_like'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.username'))
    post_id = Column(Integer, ForeignKey('post.id'))


class User(Base, UserMixin, Model):
    __tablename__ = 'users'

    # id = Column(Integer, autoincrement=True, unique=True)
    username = Column(String(50), unique=True, primary_key=True)
    email = Column(String(100), unique=True, nullable=False)
    email_verified = Column(Boolean(), default=False)
    profile_pic = Column(String(20), nullable=False, default='default.jpg')
    authy_id = Column(String(12))
    pw_hash = Column(String(200))
    phone_number = Column(String(15))
    date_created = Column(DateTime, default=datetime.utcnow)
    is_authenticated = Column(Boolean(), default=False)
    posts = relationship('Post', backref='users', lazy='joined')
    liked = relationship(
        'PostLike',
        foreign_keys='PostLike.user_id',
        backref='users', lazy='dynamic')

    def __init__(self, username=None, email=None, password=None,
                 authy_id=None, phone_number=None, is_authenticated=False):
        self.username = username
        self.email = email
        self.authy_id = authy_id
        self.phone_number = phone_number
        self.is_authenticated = is_authenticated
        self.set_password(password)
        #self.posts = posts
       # self.liked = liked

    def __repr__(self):
        return f"User('{self.username}', '{self.email}','{self.profile_pic}')"

    def set_password(self, password):
        self.pw_hash = argon2.hash(password)

    def check_password(self, password):
        return argon2.verify(password, self.pw_hash)

    def is_active(self):
        return True

    def get_id(self):
        return self.username

    def is_anonymous(self):
        return False

    @classmethod
    def load_user(cls, user_id):
        return cls.query.get(user_id)

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db_session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_name=user.username).first()
        if f:
            db_session.delete(f)

    def is_following(self, user):
        if user.username is None:
            return False
        return self.followed.filter_by(followed_name=user.username).first() is not None

    def is_followed_by(self, user):
        if user.username is None:
            return False
        return self.followers.filter_by(follower_name=user.username).first() is not None

    def get_confirm_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_name': self.username})

    def like_post(self, post):
        if not self.has_liked_post(post):
            like = PostLike(user_id=self.username, post_id=post.id)
            db_session.add(like)

    def unlike_post(self, post):
        if self.has_liked_post(post):
            PostLike.query.filter_by(
                user_id=self.username,
                post_id=post.id).delete()

    def has_liked_post(self, post):
        return PostLike.query.filter(
            PostLike.user_id == self.username,
            PostLike.post_id == post.id).count() > 0

    @staticmethod
    def verify_confrim_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_name = s.loads(token)['user_name']
        except:
            return None
        return User.query.get(user_name)


class Post(Base, UserMixin, Model):
    __tablename__ = 'post'

    id = Column(Integer, primary_key=True)
    author_id = Column(String, ForeignKey('users.username'), nullable=False)
    Title = Column(String(50), nullable=False)
    rating = Column(String(2))
    Category = Column(String(10))
    date_posted = Column(DateTime, index=True, default=datetime.utcnow)
    content = Column(Text)
    name = Column(String(2))
    likes = relationship('PostLike', backref='post', lazy='dynamic')

    def __repr__(self):
        return '<Post {}>'.format(self.content)
