# blueprints/__init__.py
from flask import Blueprint

main = Blueprint('main', __name__)
user_auth = Blueprint('user_auth', __name__)
shop = Blueprint('shop', __name__)
product = Blueprint('product', __name__)
billing = Blueprint('billing', __name__)
transactions = Blueprint('transactions', __name__)
dashboard = Blueprint('dashboard', __name__)
