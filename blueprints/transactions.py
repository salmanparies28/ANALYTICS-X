# blueprints/transactions.py
from flask import render_template
from flask_login import login_required, current_user
from . import transactions
from app import Shop, Transaction

@transactions.route('/transactions')
@login_required
def view_transactions():
    shop = Shop.query.filter_by(user_id=current_user.id).first()
    transactions = Transaction.query.filter_by(shop_id=shop.id).all()
    return render_template('transactions.html', transactions=transactions)
