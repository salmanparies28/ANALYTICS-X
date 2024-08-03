from flask import Blueprint, request, render_template, redirect, url_for
from models import db, Customer

customer_bp = Blueprint('customer', __name__)

# Route to view all customers
@customer_bp.route('/view_customers')
def view_customers():
    customers = Customer.query.all()
    return render_template('view_customers.html', customers=customers)

@customer_bp.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        email = request.form.get('email')

        if name and phone:
            new_customer = Customer(name=name, phone=phone, address=address, email=email)
            db.session.add(new_customer)
            db.session.commit()
            return redirect(url_for('customer.view_customers'))
    return render_template('add_customer.html')

