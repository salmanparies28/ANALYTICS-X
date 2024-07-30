from flask import Blueprint, request, render_template, redirect, url_for, session
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
            return redirect(url_for('auth.home'))
    return render_template('login.html')

@auth_bp.route('/home')
def home():
    if 'user_id' in session:
        return render_template('home.html', username=session['username'])
    return redirect(url_for('auth.login'))
