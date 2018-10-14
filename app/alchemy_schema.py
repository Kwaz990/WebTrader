from app import db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
from flask_login import UserMixin, login_required


@login.user_loader
def load_user(id):
   # return accounts
    return Accounts.query.get((int(id)))


class Accounts(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index= True, unique = True)
    email = db.Column(db.String(128), index= True, unique = True)
    password_hash = db.Column(db.String(128))
    balance = db.Column(db.Float)
    api_key = db.Column(db.Integer)
    holdings = db.relationship('Holdings', backref='positions', lazy ='dynamic')
    orders = db.relationship('Orders', backref='order_history', lazy='dynamic')
    watchlist = db.relationship('Watchlist', backref = 'watchlist', lazy = 'dynamic')
#    buy = db.relationship('buy', backref='buy', lazy = 'dynamic')
#    sell = db.relationship('sell', backref='sell', lazy = 'dynamic')


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<accounts> {}: {}'.format(self.id, self.username)

class Holdings(db.Model):
    id = db.Column(db.Integer, primary_key= True)
    ticker_symbol = db.Column(db.String(20))
    number_of_shares = db.Column(db.Integer)
    weighted_average_price = db.Column(db.Float)
    price_per_loss_open = db.Column(db.Float)
    price_per_loss_percent = db.Column(db.Float)
    last_price = db.Column(db.Float)
    volume_weighted_average_price = db.Column(db.Float)
    account_pk = db.Column(db.Integer, db.ForeignKey('accounts.id'))


    def __repr__(self):
        return '<holdings> ticker_symbol: {}, number_of_shares: {}, weighted_average_price: {}, price_per_loss_open: {}, price_per_loss_percent: {}, last_price: {}, VWAP: {}'.format(self.ticker_symbol, self.number_of_shares, self.price_per_loss_open, self.pricer_per_loss_percent,  self.last_price, self.volume_weighted_average_price)


class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker_symbol = db.Column(db.String(20))
    last_price = db.Column(db.Float)
    trade_volume = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    account_pk = db.Column(db.Integer, db.ForeignKey('accounts.id'))


    def __repr__(self):
        return '<orders> ticker: {}, last price: {}, volume: {}, time: {}'.format(self.ticker_symbol, self.last_price, self.trade_volume, self.timestamp)

class Watchlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker_symbol = db.Column(db.String(20))
    account_pk = db.Column(db.Integer, db.ForeignKey('accounts.id'))

    def __repr__(self):
        return '<watchlist> userID: {}, ticker: {}'.format(self.account_pk, self.ticker_symbol)
