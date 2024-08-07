# blueprints/billing.py
from flask import Blueprint, render_template, request, jsonify, session
from app import db
from models import Product, TransactionRecord, TransactionItem

billing_bp = Blueprint('billing', __name__, template_folder='templates')

@billing_bp.route('/create_bill', methods=['GET'])
def create_bill():
    session['transaction_id'] = None
    return render_template('create_bill.html')

@billing_bp.route('/start_transaction', methods=['POST'])
def start_transaction():
    if 'transaction_id' not in session or session['transaction_id'] is None:
        transaction = TransactionRecord(total_price=0)
        db.session.add(transaction)
        db.session.commit()
        session['transaction_id'] = transaction.id

    return jsonify({'status': 'success'})

@billing_bp.route('/add_product', methods=['POST'])
def add_product():
    SKU = request.form['SKU']
    quantity = int(request.form['quantity'])
    product = Product.query.filter_by(SKU=SKU).first()
    if product and quantity > 0:
        total_price = product.selling_price * quantity
        transaction_item = TransactionItem(
            transaction_id=session['transaction_id'],
            product_id=product.id,
            quantity=quantity,
            total_price=total_price
        )
        db.session.add(transaction_item)
        db.session.commit()
        # Update product stock
        product.quantity -= quantity
        db.session.commit()

        return jsonify({
            'status': 'success',
            'product_name': product.name,
            'quantity': quantity,
            'total_price': total_price
        })
    return jsonify({'status': 'error', 'message': 'Product not found or invalid quantity'})

@billing_bp.route('/finalize_bill', methods=['POST'])
def finalize_bill():
    transaction = TransactionRecord.query.get(session['transaction_id'])
    transaction.total_price = sum(item.total_price for item in transaction.items)
    transaction.customer_name = request.form['customer_name']
    transaction.customer_phone = request.form['customer_phone']
    db.session.commit()
    return jsonify({'status': 'success', 'total_price': transaction.total_price})

@billing_bp.route('/view_bill', methods=['GET'])
def view_bill():
    transaction = TransactionRecord.query.get(session['transaction_id'])
    return jsonify({
        'bill_no': transaction.bill_no,
        'customer_name': transaction.customer_name,
        'customer_phone': transaction.customer_phone,
        'date': transaction.date.strftime("%Y-%m-%d"),
        'items': [{'product_name': item.product.name, 'quantity': item.quantity, 'total_price': item.total_price} for item in transaction.items],
        'total_price': transaction.total_price
    })
