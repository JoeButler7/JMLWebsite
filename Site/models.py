from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import Model
from passlib.hash import argon2
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, backref

from .db import Base

from datetime import datetime
from flask_login import UserMixin


class User(Base):
    __tablename__ = 'users'

    # ! id = Column(Integer, unique=True, primary_key=True)
    #! username = Column(String(20), unique=True)
    username = Column(String(50), unique=True, primary_key=True)
    email = Column(String(100), unique=True, nullable=False)
    profile_pic = Column(String(20), nullable=False, default='default.jpg')
    authy_id = Column(String(12))
    pw_hash = Column(String(200))
    phone_number = Column(String(15))
    date_created = Column(DateTime, default=datetime.utcnow)
    is_authenticated = Column(Boolean(), default=False)

    # !posts = relationship('Post', backref=backref('books', lazy='dynamic'))

    # !posts = relationship('Post', backref=backref('books', lazy='dynamic'))

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


class Post(Model, UserMixin):
    __tablename__ = 'post'

    id = Column(Integer, primary_key=True)
    Title = Column(String(50), nullable=False)
    Category = Column(String(15), nullable=False)
    date_posted = Column(DateTime, index=True, default=datetime.utcnow)
    content = Column(Text)
    author_id = Column(Integer, ForeignKey('User.id'), nullable=False)

    @classmethod
    def load_post(cls, post_id):
        return cls.query.get(post_id)
