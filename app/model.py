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






