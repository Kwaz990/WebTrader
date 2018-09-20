#!/usr/bin/env python3


import sqlite3  #this is a data base manager that is included in the standad library
from app import db


connection = sqlite3.connect('example.db', check_same_thread = False)
cursor = connection.cursor()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index =True, unique = True)
    email = db.Column(db.String(120), index = True, unique = True)
    password_has = db.Column(db.String(128))


    def __repr__(self):
        return '<User {}>'.format(self.username)


# four types of operations we can do  Create Read Update Delete
#
#this is create
cursor.execute(
    """CREATE TABLE accounts(
        pk INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR,
        password VARCHAR,
        balance FLOAT,
        api_key INTEGER
    );"""
)

cursor.execute(
        """CREATE TABLE holdings(
            pk INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker_symbol VARCHAR,
            number_of_shares INTEGER,
            volume_weighted_average_price FLOAT,
            account_pk
            );"""
)
cursor.execute(
        """CREATE TABLE orders(
            pk INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker_symbol VARCHAR,
            last_price FLOAT,
            trade_volume INTEGER,
            timestamp INTEGER,
            account_pk
            );"""
)


