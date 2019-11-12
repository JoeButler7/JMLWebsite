from flask_sqlalchemy import Model
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, backref

from .db import Base
from datetime import datetime
from flask_login import UserMixin

from werkzeug.security import generate_password_hash, check_password_hash


class User(Base):
    __tablename__ = 'users'

    # !id = Column(Integer, unique=True, primary_key=True)
    # ! username = Column(String(20), unique=True)
    username = Column(String(50), unique=True, primary_key=True)
    email = Column(String(100), unique=True, nullable=False)
    profile_pic = Column(String(20), nullable=False, default='default.jpg')
    authy_id = Column(String(12))
    pw_hash = Column(String(50))
    is_authenticated = Column(Boolean(), default=False)

    # !posts = relationship('Post', backref=backref('books', lazy='dynamic'))

    def __init__(self, username=None, email=None, password=None,
                 authy_id=None, is_authenticated=False):
        self.username = username
        self.email = email
        self.authy_id = authy_id
        self.is_authenticated = is_authenticated
        self.set_password(password)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}','{self.profile_pic}')"

    def set_password(self, password):
        self.pw_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pw_hash, password)

    def is_active(self):
        return True

    def get_id(self):
        return self.username

    def is_anonymous(self):
        return False

    @classmethod
    def load_user(cls, user_id):
        return cls.query.get(user_id)


'''
class Post(Model, UserMixin):
    id = Column(Integer, primary_key=True)
    Title = Column(String(50), nullable=False)
    Category = Column(String(15), nullable=False)
    date_posted = Column(DateTime, nullable=False, default=datetime.utcnow)
    content = Column(Text)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    '''
