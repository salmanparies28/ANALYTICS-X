from flask import Blueprint, request, redirect, url_for, render_template, flash
from models import db, Customer

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        city = request.form['city']
        district = request.form['district']
        state = request.form['state']
        pincode = request.form['pincode']
        email = request.form['email']
        
        new_customer = Customer(
            name=name,
            phone=phone,
            city=city,
            district=district,
            state=state,
            pincode=pincode,
            email=email
        )
        
        db.session.add(new_customer)
        db.session.commit()
        
        flash('Customer added successfully!')
        return redirect(url_for('customer.view_customers'))
    
    return render_template('add_customer.html')

@customer_bp.route('/view_customers')
def view_customers():
    customers = Customer.query.all()
    return render_template('view_customers.html', customers=customers)
