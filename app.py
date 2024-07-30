from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange
from datetime import datetime
import os

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'a_hard_to_guess_string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///billing_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'user_auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    shops = db.relationship('Shop', backref='owner', lazy=True)

class Shop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    products = db.relationship('Product', backref='shop', lazy=True)
    transactions = db.relationship('Transaction', backref='shop', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    net_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)

# Forms
class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ShopForm(FlaskForm):
    name = StringField('Shop Name', validators=[DataRequired()])
    address = StringField('Shop Address', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    submit = SubmitField('Create Shop')

class ProductForm(FlaskForm):
    sku = StringField('SKU', validators=[DataRequired()])
    name = StringField('Product Name', validators=[DataRequired()])
    net_price = FloatField('Net Price', validators=[DataRequired()])
    selling_price = FloatField('Selling Price', validators=[DataRequired()])
    submit = SubmitField('Add Product')

class BillingForm(FlaskForm):
    sku = StringField('SKU', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Generate Bill')

# Blueprints Initialization
from blueprints.main import main as main_blueprint
from blueprints.user_auth import user_auth as user_auth_blueprint
from blueprints.shop import shop as shop_blueprint
from blueprints.product import product as product_blueprint
from blueprints.billing import billing as billing_blueprint
from blueprints.transactions import transactions as transactions_blueprint
from blueprints.dashboard import dashboard as dashboard_blueprint

app.register_blueprint(main_blueprint)
app.register_blueprint(user_auth_blueprint, url_prefix='/auth')
app.register_blueprint(shop_blueprint, url_prefix='/shop')
app.register_blueprint(product_blueprint, url_prefix='/product')
app.register_blueprint(billing_blueprint, url_prefix='/billing')
app.register_blueprint(transactions_blueprint, url_prefix='/transactions')
app.register_blueprint(dashboard_blueprint, url_prefix='/dashboard')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
