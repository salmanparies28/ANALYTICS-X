from flask import Blueprint, request, render_template, redirect, url_for, jsonify, flash, session
from models import db, TransactionRecord, TransactionItem, Product, Inventory, Customer
from datetime import datetime

billing_bp = Blueprint('billing', __name__, template_folder='templates')

def generate_bill_number():
    last_bill = TransactionRecord.query.order_by(TransactionRecord.id.desc()).first()
    if last_bill:
        return last_bill.bill_no + 1
    return 1

@billing_bp.route('/create_online_bill', methods=['GET', 'POST'])
def create_online_bill():
    if request.method == 'POST':
        try:
            organisation_id = session.get('organisation_id')
            user_email = session.get('user_email')
            if not organisation_id:
                flash('User is not logged in!', 'danger')
                return redirect(url_for('auth.login'))

            customer_phone = request.form.get('customer_phone', '')
            customer_name = request.form.get('customer_name', '')
            customer_city = request.form.get('customer_city', '')
            customer_district = request.form.get('customer_district', '')
            customer_state = request.form.get('customer_state', '')
            customer_pincode = request.form.get('customer_pincode', '')

            customer = None
            if customer_phone:
                customer = Customer.query.filter_by(phone=customer_phone).first()
                if not customer:
                    if not customer_name or not customer_pincode:
                        flash('Customer name and pincode are required for new customers.', 'danger')
                        return redirect(url_for('billing.create_online_bill'))
                    customer = Customer(
                        name=customer_name,
                        phone=customer_phone,
                        city=customer_city,
                        district=customer_district,
                        state=customer_state,
                        pincode=customer_pincode,
                        organisation_id=organisation_id
                    )
                    db.session.add(customer)
                    db.session.commit()

            product_identifiers = request.form.getlist('product_identifier[]')
            quantities = request.form.getlist('quantity[]')
            date = datetime.now().date()

            if not product_identifiers:
                flash('Missing product_identifier form field', 'danger')
                return redirect(url_for('billing.create_online_bill'))
            if not quantities:
                flash('Missing quantity form field', 'danger')
                return redirect(url_for('billing.create_online_bill'))

            total_price = 0
            items = []

            for identifier, quantity in zip(product_identifiers, quantities):
                quantity = int(quantity)
                product = Product.query.filter((Product.name.ilike(f'%{identifier}%')) | (Product.SKU.ilike(f'%{identifier}%'))).first()

                if product is None:
                    flash(f"Product not found: {identifier}", 'danger')
                    return redirect(url_for('billing.create_online_bill'))

                inventory = Inventory.query.filter_by(product_id=product.id).first()
                if inventory is None:
                    flash(f"Inventory not found for product: {identifier}", 'danger')
                    return redirect(url_for('billing.create_online_bill'))

                if inventory.quantity < quantity:
                    flash(f"Not enough inventory available for product: {identifier}", 'danger')
                    return redirect(url_for('billing.create_online_bill'))

                total_price += product.selling_price * quantity
                inventory.quantity -= quantity
                items.append((product.id, quantity, product.selling_price * quantity))

            new_bill = TransactionRecord(
                bill_no=generate_bill_number(),
                date=date,
                total_price=total_price,
                organisation_id=organisation_id,
                customer_id=customer.id if customer else None,
                billing_mode='online'
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
            flash('Online bill created successfully!', 'success')
            return redirect(url_for('billing.view_online_bills'))
        except Exception as e:
            flash(f"Error: {str(e)}", 'danger')
            return redirect(url_for('billing.create_online_bill'))

    return render_template('create_online_bill.html')


@billing_bp.route('/create_offline_bill', methods=['GET', 'POST'])
def create_offline_bill():
    if request.method == 'POST':
        try:
            organisation_id = session.get('organisation_id')
            user_email = session.get('user_email')
            if not organisation_id:
                flash('User is not logged in!', 'danger')
                return redirect(url_for('auth.login'))

            customer_phone = request.form.get('customer_phone', '')
            customer_name = request.form.get('customer_name', '')

            product_identifiers = request.form.getlist('product_identifier[]')
            quantities = request.form.getlist('quantity[]')
            date = datetime.now().date()

            if not product_identifiers:
                flash('Missing product_identifier form field', 'danger')
                return redirect(url_for('billing.create_offline_bill'))
            if not quantities:
                flash('Missing quantity form field', 'danger')
                return redirect(url_for('billing.create_offline_bill'))

            total_price = 0
            items = []

            for identifier, quantity in zip(product_identifiers, quantities):
                quantity = int(quantity)
                product = Product.query.filter((Product.name.ilike(f'%{identifier}%')) | (Product.SKU.ilike(f'%{identifier}%'))).first()

                if product is None:
                    flash(f"Product not found: {identifier}", 'danger')
                    return redirect(url_for('billing.create_offline_bill'))

                inventory = Inventory.query.filter_by(product_id=product.id).first()
                if inventory is None:
                    flash(f"Inventory not found for product: {identifier}", 'danger')
                    return redirect(url_for('billing.create_offline_bill'))

                if inventory.quantity < quantity:
                    flash(f"Not enough inventory available for product: {identifier}", 'danger')
                    return redirect(url_for('billing.create_offline_bill'))

                total_price += product.selling_price * quantity
                inventory.quantity -= quantity
                items.append((product.id, quantity, product.selling_price * quantity))

            new_bill = TransactionRecord(
                bill_no=generate_bill_number(),
                date=date,
                total_price=total_price,
                organisation_id=organisation_id,
                customer_id=None,  # No customer details are stored for offline bills
                billing_mode='offline'
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
            flash('Offline bill created successfully!', 'success')
            return redirect(url_for('billing.view_offline_bills'))
        except Exception as e:
            flash(f"Error: {str(e)}", 'danger')
            return redirect(url_for('billing.create_offline_bill'))

    return render_template('create_offline_bill.html')


@billing_bp.route('/view_online_bills')
def view_online_bills():
    organisation_id = session.get('organisation_id')
    user_email = session.get('user_email')
    if not organisation_id:
        flash('User is not logged in!', 'danger')
        return redirect(url_for('auth.login'))

    bills = db.session.query(TransactionRecord).filter_by(organisation_id=organisation_id, billing_mode='online').all()
    
    bill_items = db.session.query(
        TransactionItem,
        Product.name.label('product_name'),
        Product.SKU.label('product_sku')
    ).join(Product, TransactionItem.product_id == Product.id).all()
    
    customers = {customer.id: customer for customer in Customer.query.all()}
    
    bill_items_dict = {}
    for item in bill_items:
        if item.TransactionItem.transaction_id not in bill_items_dict:
            bill_items_dict[item.TransactionItem.transaction_id] = []
        bill_items_dict[item.TransactionItem.transaction_id].append(item)
    
    return render_template('view_online_bills.html', bills=bills, bill_items_dict=bill_items_dict, customers=customers)


@billing_bp.route('/view_offline_bills')
def view_offline_bills():
    organisation_id = session.get('organisation_id')
    user_email = session.get('user_email')
    if not organisation_id:
        flash('User is not logged in!', 'danger')
        return redirect(url_for('auth.login'))

    bills = db.session.query(TransactionRecord).filter_by(organisation_id=organisation_id, billing_mode='offline').all()
    
    bill_items = db.session.query(
        TransactionItem,
        Product.name.label('product_name'),
        Product.SKU.label('product_sku')
    ).join(Product, TransactionItem.product_id == Product.id).all()
    
    bill_items_dict = {}
    for item in bill_items:
        if item.TransactionItem.transaction_id not in bill_items_dict:
            bill_items_dict[item.TransactionItem.transaction_id] = []
        bill_items_dict[item.TransactionItem.transaction_id].append(item)
    
    return render_template('view_offline_bills.html', bills=bills, bill_items_dict=bill_items_dict)
