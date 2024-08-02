from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Organisation
import random
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        email = request.form['email']
        phone = request.form['phone']
        name = request.form['name']
        company_size = request.form['company_size']

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
            username=username,
            password=password,
            email=email,
            phone=phone,
            name=name,
            company_size=company_size,
            subscription_type=subscription_type,
            end_date=end_date
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registered successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Organisation.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            # Store user info in session
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('auth.home'))
        else:
            flash('Invalid email or password!', 'danger')
    return render_template('login.html')

@auth_bp.route('/home')
def home():
    if 'user_id' in session:
        return render_template('home.html', username=session['username'])
    return redirect(url_for('auth.login'))

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
