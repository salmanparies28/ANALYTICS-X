from flask import Blueprint, request, render_template, redirect, url_for, jsonify
from models import db, TransactionRecord, TransactionItem, Product, Inventory, Customer
from datetime import datetime

billing_bp = Blueprint('billing', __name__)

def generate_bill_number():
    last_bill = TransactionRecord.query.order_by(TransactionRecord.id.desc()).first()
    if last_bill:
        return last_bill.bill_no + 1
    return 1

@billing_bp.route('/create_bill', methods=['GET', 'POST'])
def create_bill():
    if request.method == 'POST':
        try:
            customer_id = request.form.get('customer_id')
            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            date = datetime.now().date()

            # Check for missing form fields
            if not customer_id:
                return "Missing customer_id form field", 400
            if not product_ids:
                return "Missing product_id form field", 400
            if not quantities:
                return "Missing quantity form field", 400

            total_price = 0
            items = []

            for product_id, quantity in zip(product_ids, quantities):
                quantity = int(quantity)
                product = Product.query.get(product_id)
                inventory = Inventory.query.filter_by(product_id=product_id).first()

                if product is None or inventory is None:
                    return f"Invalid product or inventory ID: {product_id}", 400

                if inventory.quantity < quantity:
                    return f"Not enough inventory available for product ID: {product_id}", 400

                total_price += product.selling_price * quantity
                inventory.quantity -= quantity
                items.append((product_id, quantity, product.selling_price * quantity))

            new_bill = TransactionRecord(
                bill_no=generate_bill_number(),
                customer_id=customer_id,
                date=date,
                total_price=total_price
            )
            db.session.add(new_bill)
            db.session.commit()

            for product_id, quantity, item_total_price in items:
                db.session.add(TransactionItem(
                    transaction_id=new_bill.id,
                    product_id=product_id,
                    quantity=quantity,
                    total_price=item_total_price
                ))

            db.session.commit()
            return redirect(url_for('billing.view_bills'))
        except Exception as e:
            return f"Error: {str(e)}", 400

    return render_template('create_bill.html')

@billing_bp.route('/view_bills')
def view_bills():
    bills = db.session.query(
        TransactionRecord,
        Customer.name.label('customer_name')
    ).join(Customer, TransactionRecord.customer_id == Customer.id).all()
    
    bill_items = db.session.query(
        TransactionItem,
        Product.name.label('product_name'),
        Product.SKU.label('product_sku')
    ).join(Product, TransactionItem.product_id == Product.id).all()
    
    return render_template('view_bills.html', bills=bills, bill_items=bill_items)

@billing_bp.route('/api/customers')
def api_customers():
    query = request.args.get('q')
    customer = Customer.query.filter_by(phone=query).first()
    if customer:
        return jsonify({"id": customer.id, "name": customer.name, "phone": customer.phone})
    return jsonify({"error": "Customer not found"})

@billing_bp.route('/api/products')
def api_products():
    query = request.args.get('q')
    product = Product.query.filter((Product.name.ilike(f'%{query}%')) | (Product.SKU.ilike(f'%{query}%'))).first()
    if product:
        return jsonify({"id": product.id, "name": product.name, "SKU": product.SKU, "price": product.selling_price})
    return jsonify({"error": "Product not found"})
