from flask_login import current_user, login_user, logout_user, login_required
from app.alchemy_schema import Accounts, Holdings, Orders
from werkzeug.urls import url_parse
from flask import render_template, flash, redirect, url_for, request, jsonify, json
from app.forms import LoginForm, RegistrationForm, MarketForm, UpdateEmailForm, UpdatePasswordForm, WithdrawForm, DepositForm, SettingsForm, OrdersForm, HoldingsForm
from app import app, db, login
from app.model import get_balance, get_holdings, get_orders, get_holding, create_holding, modify_balance, modify_holding
from app.model import create_order
from werkzeug.security import generate_password_hash, check_password_hash
import random
import requests
from functools import lru_cache
from datetime import datetime


@app.route('/bootstap')
def bootstap():
    return render_template('bootstap/index.html')



@login.user_loader
def load_user(id):
   # return accounts
    return Accounts.query.get((int(id)))


@app.route('/')
@app.route('/index/<username>')
@login_required
def index():
   # user = Accounts.query.filter_by(username=current_user).first_404()
    balance = str(get_balance(current_user.id))
   # holdings = [i for i in get_holdings(current_user.id)]
    holdings =  get_holdings(current_user.id)
    #weighted_average = weighted_average_fix(current_user.id, ticker_symbol)
   # ticker_symbol = Holdings.query.filter_by(username=current_user).get(ticker_symbol)
   # holdings = [
   #     {'positions': ticker_symbol, 'positions': number_of_shares} ]
    return render_template('bootstap/home.html', title='Home', balance = balance, holdings = holdings)


@app.route('/buy', methods=['GET', 'POST'])
@login_required
def buy(account_pk, ticker_symbol, volume):
    holding = get_holding(account_pk, ticker_symbol.upper())
    stock_price = quote(ticker_symbol.upper())
    if get_balance(account_pk) > (float(stock_price) * float(volume)):
        if holding != None:
            new_holding = holding + float(volume)
            modify_holding(account_pk, ticker_symbol.upper(), new_holding)
        else:
            create_holding(account_pk, ticker_symbol.upper(), float(volume), float(stock_price))
        new_balance = get_balance(account_pk) - (float(stock_price) * float(volume))
        modify_balance(account_pk, new_balance)
        create_order(account_pk, ticker_symbol.upper(), volume, stock_price)
        return True
    #else:
    flash('Transaction Succesful!')
    return redirect(url_for('index'))
    #flash('Transaction Failed!')
    return redirect(url_for('markets'))


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        global pk
        pk = current_user.id



@app.route('/settings')
@login_required
def settings():
    form = SettingsForm()
    return render_template('bootstap/settings.html', title='Settings', form = form)



@app.route('/sell', methods=['GET','POST'])
@login_required
def sell(account_pk, ticker_symbol, number_of_shares):
    #Does my holding have enough shares
    number_of_current_shares = get_holding(account_pk, ticker_symbol.upper())
    if number_of_current_shares == None:
        flash('Transaction Falied. You have no shares to sell.')
        return redirect(url_for('index'))
        return False
    elif number_of_current_shares < int(number_of_shares):
        flash('You do not have enough shares to complete the transaction')
        return redirect(url_for('markets'))
        return False
    else:
        #What is the share price?
        last_price = quote(ticker_symbol)
        #Calculate Remaining number of shares
        new_number_of_shares = get_holding(account_pk, ticker_symbol) - int(number_of_shares)
        #Modify our Holdings
        modify_holding(account_pk, ticker_symbol, new_number_of_shares)
        #Modify Balance
        new_amount = get_balance(account_pk) + (float(number_of_shares) * last_price)
        modify_balance(account_pk, new_amount)
        #Create Order
        create_order(account_pk, ticker_symbol, -1*int(number_of_shares), last_price)
        #Return True
        flash('Transaction succesful!')
        return redirect(url_for('index'))
        return True


@app.route('/orders', methods = ['GET', 'POST'])
@login_required
def call_orders():
    form = OrdersForm()
    if form.validate_on_submit():
        ticker = str(form.ticker_symbol.data)
        orders_specific(ticker)
       # result = get_orders(current_user.id, form.ticker_symbol.data)
        return redirect('orders_specific')
      #  return result
    return render_template('orders.html', title = 'Order History', form = form)


@app.route('/orders_specific', methods=['GET', 'POST'])
@login_required
def orders_specific():
    if request.method == 'POST':
        ticker_symbol = request.form['ticker_symbol']
        #print(ticker_symbol)
        orders = get_orders(current_user.id, ticker_symbol)
       # result = request.form
   # return orders
        return render_template('orders_specific.html', title = 'Specific Order History', orders = orders)


@app.route('/call_get_holdings', methods =['GET', 'POST'])
@login_required
def call_get_holdings():
    form = HoldingsForm()
    if form.validate_on_submit():
        ticker_symbol = form.ticker_symbol.data
        return redirect('/holdings_specific/{}'.format(ticker_symbol))
   # holdings = get_holdings(current_user.id)
    return render_template('holdings.html', title = 'Holdings', form = form)

#create a holdings form
#create a function that calls the get_holdings function with the current_user.id
@app.route('/holdings_specific/<ticker_symbol>', methods = ['GET', 'POST'])
@login_required
def holdings_specific(ticker_symbol):
  #  ticker_symbol = request.form['ticker_symbol']
    holding = get_holding(current_user.id, ticker_symbol)
    return render_template('holdings_specific.html', title= 'Specific Holdings', holding = holding)


# # FIXME: should this function be attached to a route?
# @app.route('/quote', methods=['GET', 'POST'])
@lru_cache()
def quote(ticker_symbol):
    endpoint = 'http://dev.markitondemand.com/MODApis/Api/v2/Quote/json?symbol=' + ticker_symbol
    response = requests.get(endpoint).text
    jsondata = json.loads(response)
    return jsondata.get('LastPrice')


@app.route('/update_password', methods =['GET', 'POST'])
@login_required
def update_password():
    form = UpdatePasswordForm()
    if form.validate_on_submit():
        #The checking of the password hash won't work here. Will prompt error message even upon successful change of password
        if not check_password_hash(current_user.password_hash, form.current_password.data):
            flash('This is not your current password')
        if form.new_password2.data != form.new_password.data:
            flash('New passwords do not match')
          #  return redirect(url_for('update_password'))
        new_pass = current_user.set_password(form.new_password2.data)
       # db.session.add(new_pass)
        db.session.commit()
        flash('Password succesfully updated!')
        return redirect(url_for('index'))
   # flash('An error has occured while attempting to update password.')
  #  return redirect(url_for('update_password'))
    return render_template('update_password.html', title ='Update Password', form = form)


@app.route('/update_email', methods=['GET','POST'])
@login_required
def update_email():
    form = UpdateEmailForm()
    if form.validate_on_submit():
        if form.current_email.data != current_user.email:
            flash('Incorrect current email!')
        if form.new_email2.data != form.new_email.data:
            flash('New emails do not match!')
        current_user.email = form.new_email2.data
        db.session.commit()
        flash('Email succesfully updated')
        return redirect(url_for('index'))
 #   flash('An error has occure while attempting to update email.')
#    return redirect(url_for('update_email'))
    return render_template('update_email.html', title = 'Update Email', form= form)


@app.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    form = WithdrawForm()
    if form.validate_on_submit:
       # if current_user.balance < 10.00:
        #You need to figure out how to make it work only with th euser input
       form.withdraw.data = 10.00
       if float(form.withdraw.data) > current_user.balance:
            flash('Cannot complete trasaction due to insufficient funds.')
            return redirect(url_for('index'))
       new_balance = current_user.balance - form.withdraw.data
       current_user.balance = new_balance
       db.session.commit()
       flash('Withdraw Succesful!')
       return redirect(url_for('index'))
    flash('An error has occured')
    return render_template('withdraw.html', title ='Withdraw Funds', form=form)


@app.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    form = DepositForm()
    if form.validate_on_submit():
        new_balance = current_user.balance + float(form.deposit.data)
        current_user.balance = new_balance
        db.session.commit()
        flash('Deposit Successful!')
        return redirect(url_for('index'))
    flash('An error occured')
    return render_template('deposit.html', title='Deposit Funds', form = form)


#the purpose of this function is to call the buy function with the input parameters from from.data
@app.route('/markets', methods = ['GET', 'POST'])
@login_required
def markets():
    form = MarketForm()
    if form.validate_on_submit():
        if form.buy:
            buy(current_user.id, form.ticker_symbol.data, form.volume.data)
   # flash('An error has occured. Please try again later.')
   # return redirect(url_for('markets')
        if form.sell:
            sell(current_user.id, form.ticker_symbol.data, form.volume.data)
    return render_template('markets.html',  title ='Markets', form = form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

#### Must finish register function. Do new users begin with a certain amount of money?

@app.route('/login', methods =['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Accounts.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc !='':
            next_page = url_for('index')
        return redirect(next_page)
        return redirect(url_for('index'))
    print("did not validate")
    return render_template('bootstap/login.html', title = 'Sign In', form = form)


@app.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = Accounts(username = form.username.data, email = form.email.data, password_hash = form.password.data, balance = 100.00, api_key = random.randint(10000, 99000))
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration Succesful!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form = form)


