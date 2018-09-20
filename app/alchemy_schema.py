from app import db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
from flask_login import UserMixin, login_required





@login.user_loader
def load_user(id):
    return accounts.query.get(int(id))


class accounts(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index= True, unique = True)
    email = db.Column(db.String(128), index= True, unique = True)
    password_hash = db.Column(db.String(128))
    balance = db.Column(db.Float)
    api_key = db.Column(db.Integer)
    holdings = db.relationship('holdings', backref='positions', lazy ='dynamic')
    orders = db.relationship('orders', backref='order_history', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<accounts> {}: {}'.format(self.id, self.username)

class holdings(db.Model):
    id = db.Column(db.Integer, primary_key= True)
    ticker_symbol = db.Column(db.String(20))
    number_of_shares = db.Column(db.Integer)
    volume_weighted_average_price = db.Column(db.Float)
    account_pk = db.Column(db.Integer, db.ForeignKey('accounts.id'))


    def __repr__(self):
        return '<holdings> ticker_symbol: {}, shares: {}, VWAP: {}'.format(self.ticker_symbol, self.number_of_shares, self.volume_weighted_average_price)



class orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker_symbol = db.Column(db.String(20))
    last_price = db.Column(db.Float)
    trade_volume = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    account_pk = db.Column(db.Integer, db.ForeignKey('accounts.id'))


    def __repr__(self):
        return '<accounts> {}'.format(self.username)
