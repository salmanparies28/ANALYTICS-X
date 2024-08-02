from flask import Blueprint, request, render_template, redirect, url_for
from models import db, TransactionRecord, Product, Inventory, Customer
from datetime import datetime

billing_bp = Blueprint('billing', __name__)

@billing_bp.route('/create_bill', methods=['GET', 'POST'])
def create_bill():
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        product_id = request.form['product_id']
        quantity = int(request.form['quantity'])  # Convert to integer

        # Automatically set the current date
        date = datetime.now().date()

        # Fetch the product and its inventory record
        product = Product.query.get(product_id)
        inventory = Inventory.query.filter_by(product_id=product_id).first()

        if product is None or inventory is None:
            return "Invalid product or inventory ID.", 400

        # Calculate total price
        total_price = product.selling_price * quantity

        # Check if there is enough inventory
        if inventory.quantity < quantity:
            return "Not enough inventory available.", 400

        # Update the inventory quantity
        inventory.quantity -= quantity

        # Create the new bill
        new_bill = TransactionRecord(
            customer_id=customer_id,
            product_id=product_id,
            date=date,
            quantity=quantity,
            total_price=total_price
        )
        db.session.add(new_bill)
        db.session.commit()

        return redirect(url_for('billing.view_bills'))

    products = Product.query.all()
    customers = Customer.query.all()
    return render_template('create_bill.html', products=products, customers=customers)

@billing_bp.route('/view_bills')
def view_bills():
    bills = db.session.query(
        TransactionRecord,
        Product.SKU
    ).join(Product, TransactionRecord.product_id == Product.id).all()
    return render_template('view_bills.html', bills=bills)



