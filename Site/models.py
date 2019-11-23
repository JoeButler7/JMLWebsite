from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import Model
from passlib.hash import argon2
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, backref

from .db import Base, db_session

from datetime import datetime
from flask_login import UserMixin




class Follow(Base):
    __tablename__='Follows'

    follower_name=Column(String(50),ForeignKey('users.username'), primary_key=True)
    followed_name=Column(String(50),ForeignKey('users.username'), primary_key=True)




class User(Base, UserMixin):
    __tablename__ = 'users'

    username = Column(String(50), unique=True, primary_key=True)
    email = Column(String(100), unique=True, nullable=False)
    profile_pic = Column(String(20), nullable=False, default='default.jpg')
    authy_id = Column(String(12))
    pw_hash = Column(String(200))
    phone_number = Column(String(15))
    date_created = Column(DateTime, default=datetime.utcnow)
    is_authenticated = Column(Boolean(), default=False)
    followed=relationship('Follow', foreign_keys=[Follow.follower_name], backref=backref('follower',lazy='joined'),
                        lazy='dynamic', cascade='all, delete-orphan')
    followers=relationship('Follow', foreign_keys=[Follow.followed_name], backref=backref('followed',lazy='joined'),
                        lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, username=None, email=None, password=None,
                 authy_id=None, phone_number=None, is_authenticated=False):
        self.username = username
        self.email = email
        self.authy_id = authy_id
        self.phone_number = phone_number
        self.is_authenticated = is_authenticated
        self.set_password(password)

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



class Post(Base, UserMixin):
    __tablename__ = 'Posts'

    id = Column(Integer, primary_key=True,autoincrement=True)
    Title = Column(String(50), nullable=False )
    Category = Column(String(15))
    date_posted = Column(DateTime, index=True, default=datetime.utcnow)
    content = Column(Text)

    @classmethod
    def load_post(cls, post_id):
        return cls.query.get(post_id)
