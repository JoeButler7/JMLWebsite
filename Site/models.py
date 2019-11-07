from datetime import datetime
from Site import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(uid):
    return User.query.get(int(uid))

class User(db.Model, UserMixin):
    __tablename__='user'
    id = db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(20), unique=True, nullable=False)
    email=db.Column(db.String(100), unique=True, nullable=False)
    profile_pic=db.Column(db.String(20),nullable=False, default='default.jpg')
    password=db.Column(db.String(50), nullable=False)
    posts =db.relationship('Post',backref='author',lazy=True)

    def __repr__(self):
        return f"User('{self.userrname}', '{self.email}','{self.profile_pic}')"

class Post(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    Topic=db.Column(db.String(100),nullable=False)
    date_posted=db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content=db.Column(db.Text, nullable=False)
    author_id=db.Column(db.Integer, db.ForeignKey('user.id'),nullable=False)



db.drop_all()
db.create_all()
