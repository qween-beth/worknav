import datetime
from flask_wtf import FlaskForm
from flask_login import current_user
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField,FloatField, PasswordField,\
    SubmitField, BooleanField, TextAreaField, DateField
from wtforms.validators import DataRequired, NumberRange,\
    Length, Email, EqualTo, ValidationError
from backend_frontend.models import User

# Registration Flask Form
class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

# Login Flask Form
class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


# UpdateAccount Flask Form   
class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg','jpeg','png'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')


# Review Flask Form
class ReviewForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()],\
        render_kw={"placeholder": "e.g My 'Workspace name' experience"})
    content = TextAreaField('Content', validators=[DataRequired()])
    ratings = FloatField('Ratings', validators=[DataRequired(), NumberRange(min=0, max=5)],\
        render_kw={"placeholder": "Enter rating e.g 3.5"})
    date = DateField('Date', default=datetime.datetime.now(), validators=[DataRequired()])
    submit = SubmitField('Post Review')