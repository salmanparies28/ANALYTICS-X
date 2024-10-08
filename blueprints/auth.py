import os
from flask import Blueprint, request, render_template, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Organisation
import random
from datetime import datetime, timedelta
import csv

auth_bp = Blueprint('auth', __name__)

# Get the absolute path to the current script directory
base_dir = os.path.abspath(os.path.dirname(__file__))
csv_file_path = os.path.join(base_dir, '..', 'static', 'files', 'pincodedata.csv')

# Load the pincode data into memory
pincode_data = {}
with open(csv_file_path, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        pincode_data[row['Pincode']] = {
            'city': row['Office Name'],
            'district': row['District'],  
            'state': row['StateName'],
            'country': 'India'  # Assuming the country is always India
        }

@auth_bp.route('/fetch-pincode-details', methods=['GET'])
def fetch_pincode_details():
    pincode = request.args.get('pincode')
    if pincode in pincode_data:
        return jsonify(pincode_data[pincode])
    else:
        return jsonify({'error': 'Pincode not found'})

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        password = generate_password_hash(request.form['password'])
        email = request.form['email']
        phone = request.form['phone']
        name = request.form['name']
        company_size = request.form['company_size']
        shop_name = request.form['shop_name']
        flatno = request.form['flatno']
        street = request.form['street']
        city = request.form['city']
        district = request.form['district']
        state = request.form['state']
        country = request.form['country']
        pincode = request.form['pincode']
        mobile_number = request.form['mobile_number']
        landline_number = request.form.get('landline_number')
        website_address = request.form.get('website_address')
        gst_number = request.form.get('gst_number')

        # Check if email already exists
        existing_user = Organisation.query.filter_by(email=email).first()
        if existing_user:
            flash('User already exists with this email!', 'danger')
            return redirect(url_for('auth.register'))
        
        # Assign subscription type randomly
        subscription_types = ['A', 'B', 'C', 'D']
        subscription_type = random.choice(subscription_types)
        
        # Set end date to 30 days from now
        end_date = datetime.now() + timedelta(days=30)
        
        new_user = Organisation(
            password=password,
            email=email,
            phone=phone,
            name=name,
            company_size=company_size,
            shop_name=shop_name,
            flatno=flatno,
            street=street,
            city=city,
            district=district,
            state=state,
            country=country,
            pincode=pincode,
            mobile_number=mobile_number,
            landline_number=landline_number,
            website_address=website_address,
            gst_number=gst_number,
            subscription_type=subscription_type,
            end_date=end_date
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registered successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

ADMIN_EMAIL = 'admin@techvaseegrah.com'
ADMIN_PASSWORD = 'techvaseegrah@2024!'

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['organisation_id'] = None  # No organisation ID for admin
            session['user_email'] = ADMIN_EMAIL
            session['is_admin'] = True
            flash('Logged in successfully as admin!', 'success')
            return redirect(url_for('auth.admin'))
        
        user = Organisation.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['organisation_id'] = user.id
            session['user_email'] = user.email
            session['is_admin'] = False
            flash('Logged in successfully!', 'success')
            return redirect(url_for('auth.home'))
        else:
            flash('Invalid email or password!', 'danger')
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        phone = request.form['phone']
        user = Organisation.query.filter_by(email=email, phone=phone).first()
        if user:
            session['reset_email'] = email
            flash('Email and phone number verified! You can now reset your password.', 'success')
            return redirect(url_for('auth.reset_password'))
        else:
            flash('No account found with that email and phone number combination.', 'danger')
    return render_template('forgot_password.html')

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        new_password = request.form['password']
        email = session.get('reset_email')
        user = Organisation.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            flash('Password reset successfully! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('reset_password.html')

@auth_bp.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'is_admin' not in session or not session['is_admin']:
        flash('Access denied!', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        organisation_id = request.form['organisation_id']
        additional_days = int(request.form['additional_days'])

        user = Organisation.query.get(organisation_id)
        if user:
            user.end_date += timedelta(days=additional_days)
            db.session.commit()
            flash(f'Successfully extended subscription for {user.email} by {additional_days} days.', 'success')
        else:
            flash('Organisation not found!', 'danger')

    organisations = Organisation.query.all()
    for org in organisations:
        org.remaining_days = (org.end_date - datetime.now().date()).days

    return render_template('admin.html', organisations=organisations)

@auth_bp.route('/lock')
def lock():
    return render_template('lock.html')

@auth_bp.route('/home')
def home():
    if 'organisation_id' in session:
        user = Organisation.query.get(session['organisation_id'])
        if user.end_date < datetime.now().date():  # Convert datetime to date for comparison
            return redirect(url_for('auth.lock'))
        return render_template('home.html', email=session['user_email'])
    return redirect(url_for('auth.login'))

@auth_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'organisation_id' not in session:
        flash('You must be logged in to access this page.', 'danger')
        return redirect(url_for('auth.login'))

    user = Organisation.query.get(session['organisation_id'])

    if not user:
        flash('User not found!', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        if 'update_shop' in request.form:
            # Update all shop details
            user.shop_name = request.form['shop_name']
            user.flatno = request.form['flatno']
            user.street = request.form['street']
            user.city = request.form['city']
            user.district = request.form['district']
            user.state = request.form['state']
            user.country = request.form['country']
            user.pincode = request.form['pincode']
            user.mobile_number = request.form['mobile_number']
            user.landline_number = request.form.get('landline_number')
            user.website_address = request.form.get('website_address')
            user.gst_number = request.form.get('gst_number')
            user.company_size = request.form['company_size']

            try:
                db.session.commit()
                message = 'Shop information updated successfully!'
                category = 'success'
            except Exception as e:
                db.session.rollback()
                message = 'An error occurred while updating shop details.'
                category = 'danger'
            
            return render_template('settings.html', user=user, message=message, category=category, form='updateShop')

    return render_template('settings.html', user=user)

@auth_bp.route('/update_password', methods=['POST'])
def update_password():
    if 'organisation_id' not in session:
        flash('You must be logged in to update your password.', 'danger')
        return redirect(url_for('auth.login'))

    user = Organisation.query.get(session['organisation_id'])
    if not user:
        flash('User not found!', 'danger')
        return redirect(url_for('auth.login'))

    old_password = request.form['old_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    if not check_password_hash(user.password, old_password):
        flash('Old password is incorrect.', 'danger')
    elif new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
    else:
        user.password = generate_password_hash(new_password)
        try:
            db.session.commit()
            flash('Password updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the password.', 'danger')

    return redirect(url_for('auth.settings'))

@auth_bp.route('/update_whatsapp', methods=['POST'])
def update_whatsapp():
    if 'organisation_id' not in session:
        flash('You must be logged in to update your WhatsApp number.', 'danger')
        return redirect(url_for('auth.login'))

    user = Organisation.query.get(session['organisation_id'])
    if not user:
        flash('User not found!', 'danger')
        return redirect(url_for('auth.login'))

    whatsapp_number = request.form['whatsapp_number']

    if not whatsapp_number.isdigit() or len(whatsapp_number) != 10:
        flash('Please enter a valid 10-digit WhatsApp number.', 'danger')
    else:
        user.whatsapp_number = whatsapp_number
        try:
            db.session.commit()
            flash('WhatsApp number updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the WhatsApp number.', 'danger')

    return redirect(url_for('auth.settings'))


@auth_bp.route('/new-forgot-password', methods=['GET', 'POST'])
def new_forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        phone = request.form['phone']
        user = Organisation.query.filter_by(email=email, phone=phone).first()
        if user:
            session['reset_email'] = email
            flash('Email and phone number verified! You can now reset your password.', 'success')
            return redirect(url_for('auth.reset_password'))
        else:
            flash('No account found with that email and phone number combination.', 'danger')
    return render_template('new_forgot_password.html')

