from flask import Blueprint, request, render_template, redirect, url_for, jsonify
from models import db, TransactionRecord, Product, Inventory, Customer
from datetime import datetime

billing_bp = Blueprint('billing', __name__)

@billing_bp.route('/create_bill', methods=['GET', 'POST'])
def create_bill():
    if request.method == 'POST':
        try:
            customer_id = request.form['customer_id']
            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            date = datetime.now().date()

            total_price = 0
            items = []

            for product_id, quantity in zip(product_ids, quantities):
                quantity = int(quantity)
                product = Product.query.get(product_id)
                inventory = Inventory.query.filter_by(product_id=product_id).first()

                if product is None or inventory is None:
                    return "Invalid product or inventory ID.", 400

                if inventory.quantity < quantity:
                    return f"Not enough inventory available for product ID: {product_id}", 400

                total_price += product.selling_price * quantity
                inventory.quantity -= quantity
                items.append((product_id, quantity, product.selling_price * quantity))

            new_bill = TransactionRecord(
                customer_id=customer_id,
                date=date,
                total_price=total_price
            )
            db.session.add(new_bill)
            db.session.commit()

            for product_id, quantity, item_total_price in items:
                db.session.add(TransactionRecord(
                    customer_id=customer_id,
                    product_id=product_id,
                    date=date,
                    quantity=quantity,
                    total_price=item_total_price
                ))

            db.session.commit()
            return redirect(url_for('billing.view_bills'))
        except KeyError as e:
            return f"Missing form field: {e}", 400

    return render_template('create_bill.html')

@billing_bp.route('/view_bills')
def view_bills():
    bills = db.session.query(
        TransactionRecord,
        Product.SKU
    ).join(Product, TransactionRecord.product_id == Product.id).all()
    return render_template('view_bills.html', bills=bills)

@billing_bp.route('/api/customers')
def api_customers():
    query = request.args.get('q')
    if query:
        customers = Customer.query.filter((Customer.name.ilike(f'%{query}%')) | (Customer.phone.ilike(f'%{query}%'))).all()
    else:
        customers = Customer.query.all()
    return jsonify(customers=[{"id": customer.id, "name": customer.name, "phone": customer.phone} for customer in customers])

@billing_bp.route('/api/products')
def api_products():
    query = request.args.get('q')
    if query:
        products = Product.query.filter((Product.name.ilike(f'%{query}%')) | (Product.SKU.ilike(f'%{query}%'))).all()
    else:
        products = Product.query.all()
    return jsonify(products=[{"id": product.id, "name": product.name, "SKU": product.SKU} for product in products])
