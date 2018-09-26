from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from app.alchemy_schema import Accounts, Holdings, Orders
from flask_login import current_user



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
        user=Accounts.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('This username has been taken. Please choose a different username.')

    def validate_email(self, email):
        email = Accounts.query.filter_by(email=email.data).first()
        if email is not None:
            raise ValidationError('This email has already been registered. Please use a different email.')

class MarketForm(FlaskForm):
    ticker_symbol = StringField('Ticker Symbol', validators = [DataRequired()])
    volume = StringField('Number of Shares', validators = [DataRequired()])
    price = StringField('Price per Share', validators = [DataRequired()])
    buy = BooleanField('Buy')
    sell = BooleanField('Sell')
    submit = SubmitField('Execute')

class DepositForm(FlaskForm):
    deposit = StringField('Amount to Deposit', validators=[DataRequired()])
    bank_address = StringField('Bank Routing Number')
    submit = SubmitField('Confirm Deposit')


class WithdrawForm(FlaskForm):
    withdraw = StringField('Amount to Withdraw (minimum: $10.00)', validators = [DataRequired()])
    bank_address = StringField('Bank Routing Number')
    btc_address =StringField('Bitcoin address')
    submit = SubmitField('Confirm Withdraw')


class UpdateEmailForm(FlaskForm):
    current_email = StringField('Current Email', validators = [DataRequired(), Email()])
    # if current_email != current_user_email:
    #    raise ValidationError('Incorrect Current Email!')
    new_email = StringField('New Email', validators = [DataRequired(), Email()])
    new_email2 = StringField('Confirm New Email', validators = [DataRequired(), Email(), EqualTo('new_email')])
    #if new_email2 != new_email:
     #   raise ValidationError('New emails do not match!')
    submit = SubmitField('Update Email')
    #if submit.validate_on_submit():
    #    raise ValidationError('Email succesfully updated!')
   # flash('An error occured while updateing your email.')
   # return redirect(url_for('update_email'))


class UpdatePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators = [DataRequired()])
    #if not check_password_hash(current_user.password_hash, current_password):
     #   raise ValidationError('This is not the correct current password')
       # return redirect(url_for('index'))
    new_password = PasswordField('New Password', validators = [DataRequired()])
    new_password2 = PasswordField('Confirm New Password', validators = [DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Update Password')
   # if submit.validate_on_submit():
   #     raise ValidationError('Password Succesfully Updated!')
       # return redirect(url_for('index'))
   # flash('An error occured while updating password')
   # return redirect(url_for('index'))



class HoldingsForm(FlaskForm):
    pass
