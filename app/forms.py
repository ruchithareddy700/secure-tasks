from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import (
    DataRequired, Length, Email, Regexp, EqualTo, ValidationError,
)

from .models import User


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[
        DataRequired(),
        Length(min=3, max=30),
        Regexp(r"^[A-Za-z0-9_]+$",
               message="Only letters, numbers and underscores allowed."),
    ])
    email = StringField("Email", validators=[
        DataRequired(), Email(), Length(max=120),
    ])
    password = PasswordField("Password", validators=[
        DataRequired(), Length(min=10, max=64),
    ])
    confirm = PasswordField("Confirm password", validators=[
        DataRequired(), EqualTo("password", message="Passwords must match."),
    ])

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("That username is taken.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("That email is already registered.")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=30)])
    password = PasswordField("Password", validators=[DataRequired(), Length(max=64)])