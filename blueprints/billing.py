from flask import Blueprint, request, render_template, redirect, url_for
from models import db, TransactionRecord, Customer

billing_bp = Blueprint('billing', __name__)

@billing_bp.route('/create_bill', methods=['GET', 'POST'])
def create_bill():
    if request.method == 'POST':
        shop_id = request.form['shop_id']
        customer_id = request.form['customer_id']
        product_id = request.form['product_id']
        date = request.form['date']
        quantity = request.form['quantity']
        total_price = request.form['total_price']
        new_bill = TransactionRecord(shop_id=shop_id, customer_id=customer_id, product_id=product_id, date=date, quantity=quantity, total_price=total_price)
        db.session.add(new_bill)
        db.session.commit()
        return redirect(url_for('billing.view_bills'))
    return render_template('create_bill.html')

@billing_bp.route('/view_bills')
def view_bills():
    bills = TransactionRecord.query.all()
    return render_template('view_bills.html', bills=bills)
