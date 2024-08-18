from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify
from models import db, TransactionRecord, TransactionItem, Product, Inventory, Customer
from datetime import datetime

billing_bp = Blueprint('billing', __name__, template_folder='templates')

def generate_bill_number():
    last_bill = TransactionRecord.query.order_by(TransactionRecord.id.desc()).first()
    if last_bill:
        return last_bill.bill_no + 1
    return 1
# Routes for offline bills
@billing_bp.route('/create_offline_bill', methods=['GET', 'POST'])
def create_offline_bill():
    if request.method == 'POST':
        try:
            organisation_id = session.get('organisation_id')
            if not organisation_id:
                flash('User is not logged in!', 'danger')
                return redirect(url_for('auth.login'))

            customer_phone = request.form.get('customer_phone', '')
            customer_name = request.form.get('customer_name', '')

            product_identifiers = request.form.getlist('product_identifier[]')
            quantities = request.form.getlist('quantity[]')
            date = datetime.now().date()

            if not product_identifiers or not quantities:
                flash('Product identifier and quantity are required.', 'danger')
                return redirect(url_for('billing.create_offline_bill'))

            total_price = 0
            items = []

            for identifier, quantity in zip(product_identifiers, quantities):
                quantity = int(quantity)
                product = Product.query.filter(
                    (Product.name.ilike(f'%{identifier}%')) | 
                    (Product.SKU.ilike(f'%{identifier}%'))
                ).first()

                if not product:
                    flash(f"Product not found: {identifier}", 'danger')
                    return redirect(url_for('billing.create_offline_bill'))

                inventory = Inventory.query.filter_by(product_id=product.id).first()
                if not inventory or inventory.quantity < quantity:
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
                customer_id=None,
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
            return redirect(url_for('billing.create_offline_bill'))
        except Exception as e:
            flash(f"Error: {str(e)}", 'danger')
            return redirect(url_for('billing.create_offline_bill'))

    return render_template('create_offline_bill.html')

@billing_bp.route('/edit_offline_bill/<int:bill_id>', methods=['GET'])
def edit_offline_bill(bill_id):
    organisation_id = session.get('organisation_id')
    if not organisation_id:
        flash('User is not logged in!', 'danger')
        return redirect(url_for('auth.login'))

    bill = TransactionRecord.query.filter_by(id=bill_id, organisation_id=organisation_id, billing_mode='offline').first()
    if not bill:
        flash('Bill not found!', 'danger')
        return redirect(url_for('billing.view_offline_bills'))

    bill_items = db.session.query(
        TransactionItem,
        Product.name.label('product_name')
    ).join(Product, TransactionItem.product_id == Product.id).filter(
        TransactionItem.transaction_id == bill.id
    ).all()

    return render_template('edit_offline_bill.html', bill=bill, bill_items=bill_items)

@billing_bp.route('/update_offline_bill/<int:bill_id>', methods=['POST'])
def update_offline_bill(bill_id):
    try:
        organisation_id = session.get('organisation_id')
        if not organisation_id:
            flash('User is not logged in!', 'danger')
            return redirect(url_for('auth.login'))

        bill = TransactionRecord.query.filter_by(id=bill_id, organisation_id=organisation_id, billing_mode='offline').first()
        if not bill:
            flash('Bill not found!', 'danger')
            return redirect(url_for('billing.view_offline_bills'))

        product_identifiers = request.form.getlist('product_identifier[]')
        quantities = request.form.getlist('quantity[]')

        if not product_identifiers or not quantities:
            flash('Product identifier and quantity are required.', 'danger')
            return redirect(url_for('billing.edit_offline_bill', bill_id=bill.id))

        # Remove existing items and revert inventory
        for item in bill.items:
            inventory = Inventory.query.filter_by(product_id=item.product_id).first()
            if inventory:
                inventory.quantity += item.quantity
            db.session.delete(item)

        total_price = 0
        items = []

        for identifier, quantity in zip(product_identifiers, quantities):
            quantity = int(quantity)
            product = Product.query.filter(
                (Product.name.ilike(f'%{identifier}%')) | 
                (Product.SKU.ilike(f'%{identifier}%'))
            ).first()

            if not product:
                flash(f"Product not found: {identifier}", 'danger')
                return redirect(url_for('billing.edit_offline_bill', bill_id=bill.id))

            inventory = Inventory.query.filter_by(product_id=product.id).first()
            if not inventory or inventory.quantity < quantity:
                flash(f"Not enough inventory available for product: {identifier}", 'danger')
                return redirect(url_for('billing.edit_offline_bill', bill_id=bill.id))

            total_price += product.selling_price * quantity
            inventory.quantity -= quantity
            items.append(TransactionItem(
                transaction_id=bill.id,
                product_id=product.id,
                quantity=quantity,
                total_price=product.selling_price * quantity
            ))

        bill.total_price = total_price
        db.session.add_all(items)
        db.session.commit()

        flash('Bill updated successfully!', 'success')
        return redirect(url_for('billing.view_offline_bills'))
    except Exception as e:
        flash(f"Error: {str(e)}", 'danger')
        return redirect(url_for('billing.edit_offline_bill', bill_id=bill.id))

@billing_bp.route('/search_offline_bill', methods=['GET'])
def search_offline_bill():
    organisation_id = session.get('organisation_id')
    if not organisation_id:
        flash('User is not logged in!', 'danger')
        return redirect(url_for('auth.login'))

    bill_no = request.args.get('bill_no')
    bills = []
    bill_items_dict = {}

    if bill_no:
        bills = TransactionRecord.query.filter_by(
            organisation_id=organisation_id, 
            billing_mode='offline', 
            bill_no=bill_no
        ).all()

        if bills:
            bill_ids = [bill.id for bill in bills]
            bill_items = db.session.query(
                TransactionItem,
                Product.name.label('product_name'),
                Product.SKU.label('product_sku')
            ).join(Product, TransactionItem.product_id == Product.id).filter(
                TransactionItem.transaction_id.in_(bill_ids)
            ).all()

            for item in bill_items:
                if item.TransactionItem.transaction_id not in bill_items_dict:
                    bill_items_dict[item.TransactionItem.transaction_id] = []
                bill_items_dict[item.TransactionItem.transaction_id].append(item)
    
    return render_template('view_offline_bills.html', bills=bills, bill_items_dict=bill_items_dict)

@billing_bp.route('/view_offline_bills')
def view_offline_bills():
    organisation_id = session.get('organisation_id')
    if not organisation_id:
        flash('User is not logged in!', 'danger')
        return redirect(url_for('auth.login'))

    bills = TransactionRecord.query.filter_by(organisation_id=organisation_id, billing_mode='offline').all()
    
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
