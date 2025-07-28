# app/routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models.user import User
from app.models.admin import Admin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# ---------------------
# Route: Login
# ---------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Validation
        if not (6 <= len(password) <= 12):
            flash('Password must be between 6 and 12 characters.', 'error')
            return render_template('login.html')

        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, email):
            flash('Invalid email address.', 'error')
            return render_template('login.html')

        # Check admin table first
        admin = Admin.query.filter_by(email=email).first()
        if admin and admin.check_password(password):
            session['user_id'] = admin.id
            session['role'] = 'admin'
            return redirect(url_for('admin.home'))

        # Check user table
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['role'] = 'user'
            return redirect(url_for('user.dashboard'))

        flash('Incorrect email or password!', 'error')
        return redirect(url_for('auth.login'))

    return render_template('login.html')

# ---------------------
# Route: Signup
# ---------------------
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'user')

        # Validation: username length
        if not (4 <= len(username) <= 20):
            flash('Username must be between 4 and 20 characters.', 'error')
            return render_template('signup.html')

        # Validation: password length
        if not (6 <= len(password) <= 12):
            flash('Password must be between 6 and 12 characters.', 'error')
            return render_template('signup.html')

        # Validation: email format
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, email):
            flash('Invalid email address.', 'error')
            return render_template('signup.html')

        # Check if email already exists in both tables
        existing_user = User.query.filter_by(email=email).first()
        existing_admin = Admin.query.filter_by(email=email).first()
        
        if existing_user or existing_admin:
            flash('Email already registered. Please use a different email.', 'error')
            return render_template('signup.html')

        if role == 'admin':
            # Create admin
            new_admin = Admin(
                username=username,  # Add this back
                email=email,
                password_hash=generate_password_hash(password)
            )
            db.session.add(new_admin)
        else:
            # Create regular user
            address = request.form['address']
            pin = request.form['pin']

            # Validation: PIN code (should be 6 digits)
            if not (pin.isdigit() and len(pin) == 6):
                flash('PIN code must be exactly 6 digits.', 'error')
                return render_template('signup.html')

            # Validation: address length
            if not (10 <= len(address) <= 200):
                flash('Address must be between 10 and 200 characters.', 'error')
                return render_template('signup.html')

            new_user = User(
                username=username, 
                email=email, 
                password_hash=generate_password_hash(password),
                address=address,
                pin=pin
            )
            db.session.add(new_user)
        
        db.session.commit()
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('signup.html')

# ---------------------
# Route: Logout
# ---------------------
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home.homepage'))