from flask import Blueprint, request, render_template, redirect, url_for
from models import db, TransactionRecord, Product
from datetime import datetime

billing_bp = Blueprint('billing', __name__)

@billing_bp.route('/create_bill', methods=['GET', 'POST'])
def create_bill():
    if request.method == 'POST':
        # Remove shop_id from form data
        # shop_id = request.form['shop_id']
        customer_id = request.form['customer_id']
        product_id = request.form['product_id']
        quantity = int(request.form['quantity'])  # Convert to integer

        # Automatically set the current date
        date = datetime.now().date()

        # Fetch the product to get the selling price
        product = Product.query.get(product_id)
        if product is None:
            return "Invalid product ID.", 400

        # Calculate total price
        total_price = product.selling_price * quantity

        new_bill = TransactionRecord(
            # shop_id=shop_id,
            customer_id=customer_id,
            product_id=product_id,
            date=date,
            quantity=quantity,
            total_price=total_price
        )
        db.session.add(new_bill)
        db.session.commit()
        return redirect(url_for('billing.view_bills'))
    return render_template('create_bill.html')

@billing_bp.route('/view_bills')
def view_bills():
    bills = db.session.query(
        TransactionRecord,
        Product.SKU
    ).join(Product, TransactionRecord.product_id == Product.id).all()
    return render_template('view_bills.html', bills=bills)
