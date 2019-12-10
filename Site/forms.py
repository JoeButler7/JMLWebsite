import phonenumbers


from authy import AuthyFormatException
from authy.api import AuthyApiClient

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from sqlalchemy.sql.functions import user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField
from wtforms.fields.html5 import EmailField

from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField

from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional

from phonenumbers.phonenumberutil import NumberParseException

from . import app
from Site.models import User, Post

authy_api = AuthyApiClient(app.config.get('ACCOUNT_SECURITY_API_KEY'))


class RegForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    email = EmailField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    confirm_password = PasswordField('confirm_password',
                                     validators=[DataRequired()])
    country_code = StringField('country_code', validators=[DataRequired()])
    phone_number = StringField('phone_number', validators=[DataRequired()])

    def validate_username(self, field):
        if User.query.get(field.data):
            raise ValidationError('Username already taken')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if '.' not in email.data:
            raise ValidationError('Invalid Email')
        if user:
            raise ValidationError('An account with that email already exists')

    def validate_phone_number(self, phone_number):
        user = User.query.filter_by(phone_number=phone_number.data).first()
        if user:
            raise ValidationError('An account with that phone number already exists')

    def validate_country_code(self, field):
        if not field.data.startswith('+'):
            field.data = '+' + field.data

    def validate(self):
        if not super(RegForm, self).validate():
            return False
        if self.password.data != self.confirm_password.data:
            self.errors['non_field'] = "Password and confirmation didn't match"
            return False

        phone_number = self.country_code.data + self.phone_number.data
        try:
            phone_number = phonenumbers.parse(phone_number, None)
            if not phonenumbers.is_valid_number(phone_number):
                self.phone_number.errors.append('Invalid phone number')
                return False
        except NumberParseException as e:
            self.phone_number.errors.append(str(e))
            return False
        return True


class UpdateProfileForm(FlaskForm):
    username = StringField('Username', validators=[Length(min=2, max=20), Optional()])
    email = StringField('Email', validators=[Email(), Optional()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpeg', 'png', 'jpg']), Optional()])

    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username already in use')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('An account with that email already exists')


class LoginForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    rememberme = BooleanField('Remember Me')

    def validate(self):
        if not super(LoginForm, self).validate():
            return False
        self.user = User.query.get(self.username.data)
        if not self.user or not self.user.check_password(self.password.data):
            self.errors['non_field'] = 'Invalid username and/or password'
            return False
        return True


class NewPostForm(FlaskForm):
    categories = [('Study Spot', 'Study Spot'), ('Professor', 'Professor'), ('Class', 'Class'),
                  ('Bar/Club', 'Bar/Club'), ('Restaurants', 'Restaurants'), ('Entertainment', 'Entertainment'),
                  ('Services', 'Services'), ('Libraries', 'Libraries'), ('Dining', 'Dining'),
                  ('Bathrooms', 'Bathrooms'),
                  ('Programs', 'Programs')]
    title = StringField('Title', validators=[DataRequired(), Length(min=2, max=50)])
    content = TextAreaField('Content', validators=[DataRequired()])
    rating = StringField('Rating', validators=[DataRequired()])
    # type = SelectField('Category', choices=categories)
    name = StringField('Anonymous Name', validators=[DataRequired()])
    type = SelectField('Category', choices=categories)

    submit = SubmitField('Post Review')

    author_id = User.username


class TokenVerificationForm(FlaskForm):
    token = StringField('token', validators=[DataRequired()])

    def __init__(self, authy_id):
        self.authy_id = authy_id
        super(TokenVerificationForm, self).__init__()

    def validate_token(self, field):
        try:
            verification = authy_api.tokens.verify(
                self.authy_id,
                self.token.data
            )
            if not verification.ok():
                self.token.errors.append('Invalid Token')
                return False
        except AuthyFormatException as e:
            self.token.errors.append(str(e))
            return False
        return True


class ResetPassRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email')
        if user.email_verified == False:
            raise ValidationError('That email has not yet been confrimed')


class ResetPassFrom(FlaskForm):
    password = PasswordField('password', validators=[DataRequired()])
    confirm_password = PasswordField('confirm_password',
                                     validators=[DataRequired()])
    submit = SubmitField('Request Password')


######################
# Phone Verification #
######################

class PhoneVerificationForm(FlaskForm):
    country_code = StringField('country_code', validators=[DataRequired()])
    phone_number = StringField('phone_number', validators=[DataRequired()])
    via = SelectField('via', choices=[('sms', 'SMS'), ('call', 'Call')])

    def validate_country_code(self, field):
        if not field.data.startswith('+'):
            field.data = '+' + field.data

    def validate(self):
        if not super(PhoneVerificationForm, self).validate():
            return False

        phone_number = self.country_code.data + self.phone_number.data
        try:
            phone_number = phonenumbers.parse(phone_number, None)
            if not phonenumbers.is_valid_number(phone_number):
                self.phone_number.errors.append('Invalid phone number')
                return False
        except NumberParseException as e:
            self.phone_number.errors.append(str(e))
            return False
        return True


class TokenPhoneValidationForm(FlaskForm):
    token = StringField('token', validators=[DataRequired()])
