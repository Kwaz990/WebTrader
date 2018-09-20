from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from app.alchemy_schema import accounts


class LoginForm(FlaskForm):
    username = StringField('Username', validators = [DataRequired()])
    password = PasswordField('Password', validators = [DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign in')



class RegistrationForm(FlaskForm):
    username = StringField('Username', validators = [DataRequired()])
    email = StringField('Email', validators = [DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Retype Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user=accounts.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('This username has been taken. Please choose a different username.')

    def validate_email(seld, email):
        email = accounts.query.filter_by(email=email.data).first()
        if email is not None:
            raise ValidationError('This email has already been registered. Please use a different email.')

class MarketForm(FlaskForm):
    ticker_symbol = StringField('Ticker Symbol', validators = [DataRequired()])
    volume = StringField('Number of Shares', validators = [DataRequired()])
    price = StringField('Price per Share', validators = [DataRequired()])
    buy = SubmitField('Buy')
    sell = SubmitField('Sell')

