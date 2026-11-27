from datetime import date
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Regexp, ValidationError
from flask_babel import _, lazy_gettext as _l
from app.payments import normalize_card_number, luhn_valid


class CheckoutForm(FlaskForm):
    card_number = StringField(_l('Card number'), validators=[DataRequired()],
                              render_kw={'placeholder': '6767 6767 6767 6767',
                                         'autocomplete': 'off'})
    expiry = StringField(_l('Expiry date (MM/YY)'), validators=[
        DataRequired(), Regexp(r'^(0[1-9]|1[0-2])/\d{2}$',
                               message=_l('Use the MM/YY format.'))],
        render_kw={'placeholder': '12/30', 'autocomplete': 'off'})
    cvc = StringField('CVC', validators=[
        DataRequired(), Regexp(r'^\d{3}$', message=_l('Enter 3 digits.'))],
        render_kw={'placeholder': '123', 'autocomplete': 'off'})
    submit = SubmitField(_l('Pay'))

    def validate_card_number(self, card_number):
        number = normalize_card_number(card_number.data)
        if len(number) != 16 or not luhn_valid(number):
            raise ValidationError(_('Invalid card number.'))

    def validate_expiry(self, expiry):
        month, year = expiry.data.split('/')
        today = date.today()
        if (2000 + int(year), int(month)) < (today.year, today.month):
            raise ValidationError(_('This card has expired.'))
