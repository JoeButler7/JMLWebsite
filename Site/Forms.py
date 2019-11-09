from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from Site.models import User

class RegFrom(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email =StringField('Email', validators=[DataRequired(),Email()])
    password=PasswordField('Password', validators=[DataRequired()])
    confirm_password=PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit=SubmitField('Submit')
    def validate_username(self, username):
        user =User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already in use')

    def validate_email(self, email):
        user=User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('An account with that email already exists')

class UpdateProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email =StringField('Email', validators=[DataRequired(),Email()])
    picture=FileField('Update Profile Picture', validators=[FileAllowed(['jpeg', 'png', 'jpg'])])
    submit=SubmitField('Signup')
    def validate_username(self, username):
        if username.data != current_user.username:
            user =User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username already in use')

    def validate_email(self, email):
        if email.data != current_user.email:
            user=User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('An account with that email already exists')




class LoginForm(FlaskForm):
    email=StringField('Email', validators=[DataRequired(),Email()])
    password=PasswordField('Password',validators=[DataRequired()])
    rememberme=BooleanField('Remember Me')
    submit=SubmitField('Login')


class NewPostForm(FlaskForm):
    categories=['Study Spot', 'Professor','Class', 'Bar/Club']
    title=StringField('Title', validators=[DataRequired(), Length(min=2, max=50)])
    content=TextAreaField('content', validators=[DataRequired()])
    type=SelectField('Category', choices=categories, validators=[DataRequired()])
    submit=SubmitField('Post Review')
