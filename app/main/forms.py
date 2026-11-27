from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, \
    DateTimeLocalField, IntegerField
from wtforms.validators import ValidationError, DataRequired, Length, Optional
from wtforms.widgets import HiddenInput
import sqlalchemy as sa
from flask_babel import _, lazy_gettext as _l
from app import db
from app.models import User


class EditProfileForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About me'),
                             validators=[Length(min=0, max=140)])
    email_notifications = BooleanField(
        _l('Email me about new followers, likes and messages'))
    submit = SubmitField(_l('Submit'))

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.session.scalar(sa.select(User).where(
                User.username == username.data))
            if user is not None:
                raise ValidationError(_('Please use a different username.'))


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


class PostForm(FlaskForm):
    post = TextAreaField(_l('What are you playing?'), validators=[
        DataRequired(), Length(min=1, max=140)])
    publish_at = DateTimeLocalField(_l('Publish later (GameLog Pro)'),
                                    format='%Y-%m-%dT%H:%M',
                                    validators=[Optional()])
    # зсув часового поясу браузера в хвилинах, заповнює JavaScript
    tz_offset = IntegerField(widget=HiddenInput(), default=0,
                             validators=[Optional()])
    submit = SubmitField(_l('Submit'))


class EditPostForm(FlaskForm):
    post = TextAreaField(_l('What are you playing?'), validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField(_l('Submit'))


class SearchForm(FlaskForm):
    q = StringField(_l('Search'), validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'meta' not in kwargs:
            kwargs['meta'] = {'csrf': False}
        super(SearchForm, self).__init__(*args, **kwargs)


class MessageForm(FlaskForm):
    message = TextAreaField(_l('Message'), validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField(_l('Submit'))
