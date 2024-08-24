from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from models import db, Organisation, TransactionRecord, TransactionItem, Product, Inventory, Customer
from datetime import datetime

billing_bp = Blueprint('billing', __name__, template_folder='templates')

@billing_bp.route('/create_online_bill', methods=['GET', 'POST'])
def create_online_bill():
    if request.method == 'POST':
        try:
            organisation_id = session.get('organisation_id')
            if not organisation_id:
                flash("User is not logged in!", "error")
                return redirect(url_for('auth.login'))

            # Fetch customer details from form
            customer_name = request.form['customer_name']
            customer_phone = request.form['customer_phone']
            customer_city = request.form.get('customer_city', '')
            customer_district = request.form.get('customer_district', '')
            customer_state = request.form.get('customer_state', '')
            customer_pincode = request.form['customer_pincode']
            customer_flat = request.form.get('customer_flat', '')
            customer_street = request.form.get('customer_street', '')

            # Fetch product details from form
            product_identifiers = request.form.getlist('product_identifier[]')
            quantities = request.form.getlist('quantity[]')
            date = datetime.now().date()

            if not product_identifiers or not quantities:
                flash("Product identifier and quantity are required.", "error")
                return render_template('create_online_bill.html', bill_number=generate_bill_number())

            # Check if customer exists, create new if not
            customer = Customer.query.filter_by(phone=customer_phone, organisation_id=organisation_id).first()
            if not customer:
                customer = Customer(
                    name=customer_name,
                    phone=customer_phone,
                    city=customer_city,
                    district=customer_district,
                    state=customer_state,
                    pincode=customer_pincode,
                    flat_no=customer_flat,
                    street=customer_street,
                    organisation_id=organisation_id
                )
                db.session.add(customer)
                db.session.commit()

            total_price = 0
            items = []

            # Process each product and update inventory
            for identifier, quantity in zip(product_identifiers, quantities):
                quantity = int(quantity)
                product = Product.query.filter(
                    (Product.name == identifier) | 
                    (Product.SKU == identifier)
                ).first()

                if not product:
                    flash(f"Product not found: {identifier}", "error")
                    return render_template('create_online_bill.html', bill_number=generate_bill_number())

                inventory = Inventory.query.filter_by(product_id=product.id).first()
                
                if inventory and inventory.quantity < quantity:
                    flash(f"Not enough inventory for {product.name} (SKU: {product.SKU}). Available: {inventory.quantity}, Requested: {quantity}", "error")
                    return render_template('create_online_bill.html', bill_number=generate_bill_number())

                if inventory:
                    total_price += product.selling_price * quantity
                    inventory.quantity -= quantity
                    items.append((product.id, quantity, product.selling_price * quantity))
                else:
                    flash(f"No inventory record found for {product.name} (SKU: {product.SKU}).", "error")
                    return render_template('create_online_bill.html', bill_number=generate_bill_number())

            # Create and save new bill
            new_bill = TransactionRecord(
                bill_no=generate_bill_number(),
                date=date,
                total_price=total_price,
                organisation_id=organisation_id,
                customer_id=customer.id,
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

            flash("Online bill created successfully! Please review the bill before finalizing.", "success")
            return redirect(url_for('billing.view_online_bills'))
        except Exception as e:
            db.session.rollback()  # Rollback in case of any exception
            flash(f"Error: {str(e)}", "error")
            return render_template('create_online_bill.html', bill_number=generate_bill_number())

    bill_number = generate_bill_number()
    return render_template('create_online_bill.html', bill_number=bill_number)

@billing_bp.route('/finalize_bill/<int:bill_id>', methods=['POST'])
def finalize_bill(bill_id):
    try:
        organisation_id = session.get('organisation_id')
        if not organisation_id:
            flash("User is not logged in!", "error")
            return redirect(url_for('auth.login'))

        bill = TransactionRecord.query.get(bill_id)
        if not bill or bill.organisation_id != organisation_id:
            flash("Bill not found!", "error")
            return redirect(url_for('billing.view_online_bills'))

        # Finalize the bill (e.g., mark it as finalized)
        bill.status = 'finalized'  # Assuming you have a 'status' field
        db.session.commit()

        flash("Bill finalized successfully!", "success")
        return redirect(url_for('billing.view_online_bills'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('billing.view_online_bills'))

@billing_bp.route('/view_online_bills')
def view_online_bills():
    try:
        organisation_id = session.get('organisation_id')
        if not organisation_id:
            flash("User is not logged in!", "error")
            return redirect(url_for('auth.login'))

        bills = TransactionRecord.query.filter_by(organisation_id=organisation_id, billing_mode='online').all()

        customers = {customer.id: customer for customer in Customer.query.all()}
        
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
        
        return render_template('view_online_bills.html', bills=bills, customers=customers, bill_items_dict=bill_items_dict)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('billing.view_online_bills'))

def generate_bill_number():
    last_bill = TransactionRecord.query.order_by(TransactionRecord.id.desc()).first()
    if last_bill:
        return last_bill.bill_no + 1
    return 1

# Offline Bill Routes
@billing_bp.route('/create_offline_bill', methods=['GET', 'POST'])
def create_offline_bill():
    if request.method == 'POST':
        try:
            organisation_id = session.get('organisation_id')
            if not organisation_id:
                flash("User is not logged in!", "error")
                return redirect(url_for('auth.login'))

            customer_phone = request.form.get('customer_phone', '')
            customer_name = request.form.get('customer_name', '')

            product_identifiers = request.form.getlist('product_identifier[]')
            quantities = request.form.getlist('quantity[]')
            date = datetime.now().date()

            if not product_identifiers or not quantities:
                flash("Product identifier and quantity are required.", "error")
                return redirect(url_for('billing.create_offline_bill'))

            total_price = 0
            items = []
            invalid_products = []

            for identifier, quantity in zip(product_identifiers, quantities):
                quantity = int(quantity)
                product = Product.query.filter(
                    (Product.name == identifier) | 
                    (Product.SKU == identifier)
                ).first()

                if not product:
                    invalid_products.append(f"Product not found: {identifier}")
                    continue

                inventory = Inventory.query.filter_by(product_id=product.id).first()
                if not inventory or inventory.quantity < quantity:
                    invalid_products.append(f"Not enough inventory for product: {identifier} (Available: {inventory.quantity if inventory else 0}, Requested: {quantity})")
                    continue

                total_price += product.selling_price * quantity
                inventory.quantity -= quantity  # Decrease the inventory
                items.append((product.id, quantity, product.selling_price * quantity))

            if invalid_products:
                flash("Errors found in the bill: " + "; ".join(invalid_products), "error")
                return redirect(url_for('billing.create_offline_bill'))

            # Create the bill if no errors
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
            flash("Offline bill created successfully!", "success")
            return redirect(url_for('billing.create_offline_bill'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for('billing.create_offline_bill'))
        
    return render_template('create_offline_bill.html')

@billing_bp.route('/edit_offline_bill/<int:bill_id>', methods=['GET'])
def edit_offline_bill(bill_id):
    try:
        organisation_id = session.get('organisation_id')
        if not organisation_id:
            flash("User is not logged in!", "error")
            return redirect(url_for('auth.login'))

        bill = TransactionRecord.query.filter_by(id=bill_id, organisation_id=organisation_id, billing_mode='offline').first()
        if not bill:
            flash("Bill not found!", "error")
            return redirect(url_for('billing.view_offline_bills'))

        bill_items = db.session.query(
            TransactionItem,
            Product.name.label('product_name')
        ).join(Product, TransactionItem.product_id == Product.id).filter(
            TransactionItem.transaction_id == bill.id
        ).all()

        return render_template('edit_offline_bill.html', bill=bill, bill_items=bill_items)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('billing.view_offline_bills'))

@billing_bp.route('/update_offline_bill/<int:bill_id>', methods=['POST'])
def update_offline_bill(bill_id):
    try:
        organisation_id = session.get('organisation_id')
        if not organisation_id:
            flash("User is not logged in!", "error")
            return redirect(url_for('auth.login'))

        bill = TransactionRecord.query.filter_by(id=bill_id, organisation_id=organisation_id, billing_mode='offline').first()
        if not bill:
            flash("Bill not found!", "error")
            return redirect(url_for('billing.view_offline_bills'))

        product_identifiers = request.form.getlist('product_identifier[]')
        quantities = request.form.getlist('quantity[]')

        if not product_identifiers or not quantities:
            flash("Product identifier and quantity are required.", "error")
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
                (Product.name == identifier) | 
                (Product.SKU == identifier)
            ).first()

            if not product:
                flash(f"Product not found: {identifier}", "error")
                return redirect(url_for('billing.edit_offline_bill', bill_id=bill.id))

            inventory = Inventory.query.filter_by(product_id=product.id).first()
            if not inventory or inventory.quantity < quantity:
                flash(f"Not enough inventory available for product: {identifier}", "error")
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

        flash("Bill updated successfully!", "success")
        return redirect(url_for('billing.view_offline_bills'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('billing.edit_offline_bill', bill_id=bill.id))

@billing_bp.route('/search_offline_bill', methods=['GET'])
def search_offline_bill():
    try:
        organisation_id = session.get('organisation_id')
        if not organisation_id:
            flash("User is not logged in!", "error")
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
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('billing.view_offline_bills'))

@billing_bp.route('/view_offline_bills')
def view_offline_bills():
    try:
        organisation_id = session.get('organisation_id')
        if not organisation_id:
            flash("User is not logged in!", "error")
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
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('billing.view_offline_bills'))

@billing_bp.route('/search_online_bill', methods=['GET'])
def search_online_bill():
    try:
        organisation_id = session.get('organisation_id')
        if not organisation_id:
            flash("User is not logged in!", "error")
            return redirect(url_for('auth.login'))

        bill_no = request.args.get('bill_no', '').strip()
        
        if not bill_no:
            flash("Please enter a bill number to search.", "error")
            return redirect(url_for('billing.view_online_bills'))

        bills = TransactionRecord.query.filter_by(organisation_id=organisation_id, bill_no=bill_no, billing_mode='online').all()

        if not bills:
            flash(f"No bills found for Bill Number: {bill_no}", "error")
            return redirect(url_for('billing.view_online_bills'))

        customers = {customer.id: customer for customer in Customer.query.all()}
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

        return render_template('view_online_bills.html', bills=bills, customers=customers, bill_items_dict=bill_items_dict)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('billing.view_online_bills'))
