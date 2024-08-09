from flask import Blueprint, request, redirect, url_for, render_template, flash, session
from models import db, Customer
from flask import jsonify

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        name = request.form['name']
        pincode = request.form['pincode']
        phone = request.form['phone']
        city = request.form['city']
        district = request.form['district']
        state = request.form['state']
        email = request.form['email']

        organisation_id = session.get('organisation_id')
        user_email = session.get('user_email')
        if not organisation_id:
            flash('User is not logged in!', 'danger')
            return redirect(url_for('auth.login'))
        
        new_customer = Customer(
            name=name,
            phone=phone,
            city=city,
            district=district,
            state=state,
            pincode=pincode,
            email=email,
            organisation_id=organisation_id
        )
        
        db.session.add(new_customer)
        db.session.commit()
        
        flash('Customer added successfully!')
        return redirect(url_for('auth.home'))
    
    return render_template('add_customer.html')



@customer_bp.route('/view_customers')
def view_customers():
    organisation_id = session.get('organisation_id')
    user_email = session.get('user_email')
    if not organisation_id:
        flash('User is not logged in!', 'danger')
        return redirect(url_for('auth.login'))

    customers = Customer.query.filter_by(organisation_id=organisation_id).all()
    return render_template('view_customers.html', customers=customers)

@customer_bp.route('/edit_customer/<int:id>', methods=['GET', 'POST'])
def edit_customer(id):
    customer = Customer.query.get_or_404(id)
    organisation_id = session.get('organisation_id')
    user_email = session.get('user_email')
    if not organisation_id:
        flash('User is not logged in!', 'danger')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        customer.name = request.form['name']
        customer.pincode = request.form['pincode']
        customer.phone = request.form['phone']
        customer.city = request.form['city']
        customer.district = request.form['district']
        customer.state = request.form['state']
        customer.email = request.form['email']
        
        db.session.commit()
        
        flash('Customer updated successfully!')
        return redirect(url_for('customer.view_customers'))
    
    return render_template('edit_customer.html', customer=customer)

@customer_bp.route('/customer.edit_customer', methods=['POST'])
def check_phone():
    phone = request.form.get('phone')
    organisation_id = session.get('organisation_id')
    user_email = session.get('user_email')

    if not organisation_id:
        return jsonify({'exists': False})

    exists = Customer.query.filter_by(phone=phone, organisation_id=organisation_id).first() is not None
    return jsonify({'exists': exists})

@customer_bp.route('/delete_customer/<int:id>', methods=['POST'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    organisation_id = session.get('organisation_id')
    user_email = session.get('user_email')
    if not organisation_id:
        flash('User is not logged in!', 'danger')
        return redirect(url_for('auth.login'))

    db.session.delete(customer)
    db.session.commit()
    
    flash('Customer deleted successfully!')
    return redirect(url_for('customer.view_customers'))
