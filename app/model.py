#!/bin/usr/env python3

import time, sqlite3, requests, json, uuid
from functools import lru_cache
from app import app, db
from flask import render_template, flash, redirect, url_for, request, jsonify, json
from app.forms import LoginForm, RegistrationForm, MarketForm, UpdateEmailForm, UpdatePasswordForm, WithdrawForm, DepositForm, SettingsForm, OrdersForm, HoldingsForm
from random import randint
from flask_login import current_user, login_user, logout_user, login_required
from app.alchemy_schema import Accounts, Holdings, Orders
from werkzeug.urls import url_parse
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import random



@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        global pk
        pk = current_user.id

@app.route('/')
@app.route('/index/<username>')
@login_required
def index():
   # user = Accounts.query.filter_by(username=current_user).first_404()
    balance = str(get_balance(current_user.id))
   # holdings = [i for i in get_holdings(current_user.id)]
    holdings =  get_holdings(current_user.id)
   # ticker_symbol = Holdings.query.filter_by(username=current_user).get(ticker_symbol)
   # holdings = [
   #     {'positions': ticker_symbol, 'positions': number_of_shares} ]
    return render_template('index.html', title='Home', balance = balance, holdings = holdings)



@app.route('/settings')
@login_required
def settings():
    form = SettingsForm()
    return render_template('settings.html', title='Settings', form = form)



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
    return render_template('login.html', title = 'Sign In', form = form)
   # global pk
   # pk == current_user.id
   # return pk

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

#### Must finish register function. Do new users begin with a certain amount of money?

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
        return redirct(url_for('index'))
 #   flash('An error has occure while attempting to update email.')
#    return redirect(url_for('update_email'))
    return render_template('update_email.html', title = 'Update Email', form= form)

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



def connect():
    global dbname
    dbname = 'webtrader.db'
    global connection
    connection = sqlite3.connect(dbname)
    global cursor
    cursor=connection.cursor()
    return connection, cursor


def close(connection, cursor):
    connection.commit()
    cursor.close()
    connection.close()


#global pk
#pk = current_user.username.id


#FINISH THIS GET_PK FUNCTION
def get_pk():
    connection, cursor = connect()
    SQL = "SELECT pk FROM Accounts WHERE username = ?"
    values  = (username,)
    cursor.excecute(SQL, values)
    answer = cursor.fetchone()
    close(connection, cursor)
    if answer == None:
        return None
    return answer[0]


@app.route('/quote', methods=['GET', 'POST'])
@lru_cache()
def quote(ticker_symbol):
    endpoint = 'http://dev.markitondemand.com/MODApis/Api/v2/Quote/json?symbol=' + ticker_symbol
    response = requests.get(endpoint).text
    jsondata = json.loads(response)
    return jsondata.get('LastPrice')


def login(username, password):
    connection, cursor = connect()
    SQL = "SELECT pk FROM Accounts WHERE username = ? AND password = ?"
    values = (username, password)
    cursor.execute(SQL, values)
    testvar = cursor.fetchone()
    close(connection, cursor)
    if testvar == None:
        return None
    else:
        return testvar[0]


def get_api(pk):
    connection, cursor = connect()
    SQL = '''SELECT api_key FROM Accounts WHERE pk = ?'''
    values = (pk,)
    cursor.execute(SQL, values)
    api = cursor.fetchone()
    close(connection, cursor)
    if api == None:
        return None
    else:
        return api[0]



def get_pk_username(api_key):
    connection, cursor = connect()
    SQL = ''' SELECT pk, username FROM Accounts WHERE api_key = ?'''
    values = (api_key,)
    cursor.execute(SQL, values)
    pk_username = cursor.fetchone()
    close(connection, cursor)
    if pk_username == None:
        return None, None
    else:
        return int(pk_username[0]), pk_username[1]



def save_create_account(username, password, balance):
    connection, cursor = connect()
    funds = balance
    api_key = random.randint(10000, 99000)
    SQL2 = '''INSERT INTO Accounts (username, password, balance, api_key) VALUES(?, ?, ?, ?)'''
    values2 = (username, password, funds, api_key)
    cursor.execute(SQL2, values2)
    close(connection, cursor)




def get_accounts():
    connection, cursor = connect()
    SQL = '''SELECT pk, username, password, balance, api_key FROM Accounts'''
    cursor.execute(SQL)
    accounts = cursor.fetchall()
    accounts_list = []
    close(connection, cursor)
    for i in accounts:
        accounts_list.append(i)
    return accounts_list




def get_balance(pk):
   connection, cursor = connect()
   sql = "SELECT balance FROM Accounts WHERE id = ?"
   cursor.execute(sql, (pk,))
   balance = cursor.fetchone()
   close(connection, cursor)
   if balance == None:
       return None
   else:
       return balance[0]

# must create holdings_specific html page
@app.route('/holdings_specific/<ticker_symbol>', methods = ['GET', 'POST'])
@login_required
def holdings_specific(ticker_symbol):
  #  ticker_symbol = request.form['ticker_symbol']
    holding = get_holding(current_user.id, ticker_symbol)
    return render_template('holdings_specific.html', title= 'Specific Holdings', holding = holding)


#create a holdings form
#create a function that calls the get_holdings function with the current_user.id
@app.route('/call_get_holdings', methods =['GET', 'POST'])
@login_required
def call_get_holdings():
    form = HoldingsForm()
    if form.validate_on_submit():
        ticker_symbol = form.ticker_symbol.data
        return redirect(url_for('holdings_specific', ticker_symbol=ticker_symbol))
   # holdings = get_holdings(current_user.id)
    return render_template('holdings.html', title = 'Holdings', form = form)


#TO DO remove the automatic Vwap for user with pk 1
def get_holdings(pk):
    connection, cursor = connect()
    # if pk == 1:
    #     input_vwap_TSLA(pk, 'TSLA')
    #     input_vwap_AAPL(pk, 'AAPL')
    SQL = "SELECT ticker_symbol, number_of_shares, weighted_average_price, price_per_loss_open, price_per_loss_percent, last_price, volume_weighted_average_price FROM Holdings WHERE account_pk = ?"
    values = (pk,)
    cursor.execute(SQL, values)
    testvar2 = cursor.fetchall()
    result = []
    close(connection, cursor)
    for row in testvar2:
        dic = {
            "ticker_symbol":row[0],
            "number_of_shares":row[1],
            "weighted_average_price":row[2],
            "price_per_loss_open": row[3],
            "price_per_loss_percent": row[4],
            'last_price': row[5],
            'volume_weighted_average_price': row[6]
        }
        result.append(dic)
        #result.append(row)
    return testvar2
   # return result
    #return row


def weighted_average_price():
    connection, cursor = connect()
    sql = '''SELECT trade_volume, last_price FROM Orders WHERE pk = ?, ticker_symbol = ?'''
    values = (pk, ticker_symbol)
    cursor.execute(sql, values)
    volume_and_price = cursor.fetchall()
    lst = []
    total_shares = 0
    close(connection, cursor)
    for i in volume_and_price:
        for _ in i:
            vol = _[0]
            price = _[1]
            total_shares += vol
        lst.append([vol*price])
    weight = sum(lst)
    weighted_average = weight/total_shares
    sql_input = '''UPDATE Holdings SET weighted_average_price = ? WHERE pk = ? '''
    input_values = (weighted_average, pk)
    cursor.execute()
    close(connnection, cursor)






def get_holding(pk, ticker_symbol):
    connection, cursor = connect()
    sql = '''SELECT number_of_shares FROM Holdings WHERE account_pk = ? and ticker_symbol = ?'''
    values = (pk, ticker_symbol.upper())
    cursor.execute(sql,values)
    holding = cursor.fetchall()
    holding_list = []
    close(connection, cursor)
    for i in holding:
        if holding == None:
            return None
        else:
           return i[0]


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


def get_orders(pk, ticker_symbol, cutoff = '1970-01-01'):
    connection, cursor = connect()
    SQL = '''SELECT ticker_symbol, last_price, trade_volume, timestamp FROM
 Orders WHERE account_pk = ? AND ticker_symbol = ? AND timestamp >= ?;'''
    # for the cutoff_convert datetime.datetime was changed to datetime.
    cutoff_convert = int(time.mktime(datetime.strptime(cutoff, "%Y-%m-%d").timetuple()))
    values = (pk, ticker_symbol, cutoff_convert) #cutoff should be a string in yyyy-mm-dd format
    cursor.execute(SQL, values)
    lst = []
    rows = cursor.fetchall() #What data structure does rows return as? a list, or dict?
    close(connection, cursor)
    for i in rows:
        if rows == None:
            return None
        d = {
        'ticker_symbol': i[0],
        'last_price': i[1],
        'trade_volume': i[2],
        'timestamp': '{}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(i[3]))))}
        lst.append(d)
   # return d
 #   return rows
    return lst
    #return tuple(rows)

def create_holding(account_pk, ticker_symbol, number_of_shares, price):
    connection, cursor = connect()
    SQL = '''INSERT INTO Holdings (account_pk, ticker_symbol, number_of_shares, volume_weighted_average_price)
VALUES (?, ?, ?, ?)'''
    values = (account_pk, ticker_symbol.upper(), number_of_shares, create_vwap(account_pk, ticker_symbol, number_of_shares, price))
    cursor.execute(SQL, values)
    close( connection, cursor)
    return True

def get_price(account_pk, ticker_symbol):
    SQL = '''SELECT last_price FROM Orders WHERE account_pk = ? AND ticker_symbol =?'''
    values = (account_pk, ticker_symbol)
    cursor.execute(SQL, values)
    prices = cursor.fetchall()
    sum_prices = 0.00
    for i in prices:
        sum_prices += int(i[0])
    return sum_prices

def get_trade_volume(account_pk, ticker_symbol):
    connection, cursor = connect()
    SQL = '''SELECT trade_volume FROM Orders WEHRE account_pk =? AND ticker_symbol = ?'''
    values = (account_pk, ticker_symbol)
    cursor.execute(SQL, values)
    close(connection, cursor)


def select_all_tickers(account_pk):
    connection, cursor = connect()
    SQL = '''SELECT ticker_symbol FROM Holdings WHERE account_pk = ?'''
    values = (account_pk,)
    cursor.execute(SQL, values)
    all_tickers = cursor.fetchall()
    ticker_list = []
    close(connection, cursor)
    for i in all_tickers:
        ticker_list.append(i)
    return ticker_list

# def input_vwap_TSLA(account_pk, ticker_symbol):
#     connection, cursor = connect()
#     SQL = '''SELECT last_price, trade_volume FROM Orders WHERE account_pk = ?
# AND ticker_symbol = ?'''
#     values = (account_pk, ticker_symbol)
#     cursor.execute(SQL, values)
#     price_volume = cursor.fetchall()
#     sum_buys_trade_volume = 0
#     sum_trade_volume = 0
#     for i in price_volume:
#         if float(i[0]) > 0:
#             sum_buys_trade_volume += (float(i[0]) *float(i[1]))
#             sum_trade_volume += float(i[1])
#     vwap = (sum_buys_trade_volume/sum_trade_volume)
#     SQL_input = '''UPDATE Holdings SET volume_weighted_average_price = ?
#  WHERE account_pk = ? AND ticker_symbol = ?'''
#     values_input = (vwap, account_pk, 'TSLA')
#     cursor.execute(SQL_input, values_input)
#     close(connection, cursor)


# def input_vwap_AAPL(account_pk, ticker_symbol):
#     connection, cursor = connect()
#     SQL = '''SELECT last_price, trade_volume FROM Orders WHERE account_pk = ?
# AND ticker_symbol = ?'''
#     values = (account_pk, ticker_symbol)
#     cursor.execute(SQL, values)
#     price_volume = cursor.fetchall()
#     sum_buys_trade_volume = 0
#     sum_trade_volume = 0
#     for i in price_volume:
#         if float(i[0]) > 0:
#             sum_buys_trade_volume += (float(i[0]) *float(i[1]))
#             sum_trade_volume += float(i[1])
#     vwap = (sum_buys_trade_volume/sum_trade_volume)
#     SQL_input = '''UPDATE Holdings SET volume_weighted_average_price = ?
#  WHERE account_pk = ? AND ticker_symbol = ?'''
#     values_input = (vwap, account_pk, 'AAPL')
#     cursor.execute(SQL_input, values_input)
#     close(connection, cursor)


def create_vwap(account_pk, ticker_symbol, number_of_shares, price):
    volume_x_price = number_of_shares * price
    vwap = volume_x_price / number_of_shares
    return vwap



def modify_vwap(account_pk, ticker_symbol, number_of_shares):
    connection, cursor = connect()
    #endpoint = 'http://dev.markitondemand.com/MODApis/Api/v2/Quote/json?symbol=' + ticker_symbol
    #response = requests.get(endpoint).text
    #jsondata = json.loads(response)
    price = get_price(account_pk, ticker_symbol)
    #total_market_volume = jsondata.get('Volume', None)
    SQL = '''SELECT last_price, trade_volume From Orders WHERE account_pk = ?
AND ticker_symbol = ?'''
    values = (account_pk, ticker_symbol)
    cursor.execute(SQL, values)
    price_volume = cursor.fetchall()
    sum_buys_trade_volume = 0
    sum_trade_volume = 0
    close(connection, cursor)
    for i in price_volume:
        if price_volume == None:
            return None
        else:
            print(i)
            if float(i[0]) > 0:
                sum_buys_trade_volume += (float(i[0]) * float(i[1]))
                sum_trade_volume += int(i[1])
    #print(sum_buys_trade_volume)
                VWAP = (sum_buys_trade_volume/sum_trade_volume)
                return VWAP

def TWAP(ticker_symbol):
    endpoint = 'http://dev.markitondemand.com/MODApis/Api/v2/Quote/json?symbol=' + ticker_symbol
    response = requests.get(endpoint).text
    jsondata = json.loads(response)
    high = jsondata.get('High', None)
    low = jsondata.get('Low', None)
    close = jsondata.get('LastPrice', None)
    TWAP = (int(high) + int(low) +int(close))/3
    return TWAP

def modify_holding(account_pk, ticker_symbol, number_of_shares):
    connection, cursor = connect()
    SQL = '''UPDATE Holdings SET number_of_shares = ?, volume_weighted_average_price =?
WHERE ticker_symbol = ? AND  account_pk = ?'''
    values = (number_of_shares, modify_vwap(account_pk, ticker_symbol, number_of_shares), ticker_symbol, account_pk)
    cursor.execute(SQL, values)
    close(connection, cursor)


def modify_holding_api(api_key, ticker_symbol, number_of_shares):
    connection, cursor = connect()
    SQL = '''UPDATE Holdings SET number_of_shares = ?, volume_weighted_average_price =?
WHERE ticker_symbol = ? AND  api_key = ?'''
    values = (number_of_shares, modify_vwap_api(api_key, ticker_symbol, number_of_shares), ticker_symbol, api_key)
    cursor.execute(SQL, values)
    close(connection, cursor)


def modify_balance(account_pk, new_amount):
    connection, cursor = connect()
    SQL = '''UPDATE Accounts SET balance = ? WHERE id = ?'''
    cursor.execute(SQL,(new_amount, account_pk))
    close(connection, cursor)


def modify_balance_api(api_key, new_amount):
    connection, cursor = connect()
    SQL = '''UPDATE Accounts SET balance = ? WHERE api_key = ?'''
    cursor.execute(SQL,(new_amount, api_key))
    close(connection, cursor)



def create_order(account_pk, ticker_symbol, trade_volume, last_price):
    connection, cursor = connect()
    SQL = '''INSERT INTO Orders (account_pk, ticker_symbol, last_price, trade_volume, timestamp)
            VALUES (?, ?, ?, ?, ?)'''
    values = (account_pk, ticker_symbol.upper(), last_price, trade_volume, int(time.time()))
    cursor.execute(SQL,values)
    close(connection, cursor)


def create_order_api(api_key, ticker_symbol, trade_volume, last_price):
    SQL = '''INSERT INTO Orders (api_key, ticker_symbol, last_price, trade_volume, timestamp)
            VALUES (?, ?, ?, ?, ?)'''
    values = (api_key, ticker_symbol.upper(), last_price, trade_volume, int(time.time()))
    cursor.execute(SQL,values)
    connection.commit()


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
    else:
        flash('Transaction Succesful!')
        return redirect(url_for('index'))
    #flash('Transaction Failed!')
    return redirect(url_for('markets'))


def buy_api(api_key):
   api_key = api_key
   holding = get_holding_api(api_key, ticker_symbol.upper())
   stock_price = quote(ticker_symbol.upper())
   if get_balance_api(api_key) > (float(stock_price) * float(volume)):
       if holding != None:
           new_holding = holding + volume
           modify_holding_api(api_key, ticker_symbol.upper(), new_holding, stock_price)
       else:
           create_holding_api(api_key, ticker_symbol.upper(), volume, stock_price)

       new_balance = get_balance_api(api_key) - (stock_price *volume)
       modify_balance_api(api_key, new_balance)
       create_order_api(api_key, ticker_symbol.upper(), volume, stock_price)
       return True
   else:
       return False





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
        create_order(account_pk, ticker_symbol, int(number_of_shares), last_price)
        #Return True
        flash('Transaction succesful!')
        return redirect(url_for('index'))
        return True
