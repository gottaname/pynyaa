
from flask_wtf import FlaskForm
from wtforms import (
    StringField, FileField, TextAreaField, SelectField, PasswordField
)
from wtforms.validators import DataRequired, Email


class UploadTorrentForm(FlaskForm):
    torrent = FileField(validators=[DataRequired()])
    category = SelectField(validators=[DataRequired()])
    website = StringField()
    description = TextAreaField()


class SignUpForm(FlaskForm):
    username = StringField(validators=[DataRequired()])
    password = PasswordField(validators=[DataRequired()])
    email = StringField(validators=[DataRequired(), Email()])


class LoginForm(FlaskForm):
    email = StringField(validators=[DataRequired(), Email()])
    password = PasswordField(validators=[DataRequired()])
