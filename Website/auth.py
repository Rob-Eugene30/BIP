from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db   ##means from __init__.py import db
from flask_login import login_user, login_required, logout_user, current_user


auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    print(f"DEBUG: current_user = {current_user}")  # Debug line
    print(f"DEBUG: session = {session}")  # Debug line

    if current_user.is_authenticated:  # Add this check
        flash('You are already logged in!', category='info')
        return redirect(url_for('views.home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=False)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    print(f"DEBUG: Before logout - current_user = {current_user}")  # Debug line
    print(f"DEBUG: Before logout - session = {session}")  # Debug line
    
    logout_user()  # Log out the user
    session.clear()  # Clear the session
    
    print(f"DEBUG: After logout - current_user = {current_user}")  # Debug line
    print(f"DEBUG: After logout - session = {session}")  # Debug line
    
    # Explicitly clear the Flask-Login cookie
    response = redirect(url_for('views.welcome'))
    response.delete_cookie('session')  # Clear the session cookie
    response.delete_cookie('remember_token')  # Clear the remember token cookie


    return response


@auth.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if current_user.is_authenticated:  # Add this check
        flash('You are already logged in!', category='info')
        return redirect(url_for('views.home'))

    if request.method == 'POST':
        email = request.form.get('email')
        firstName = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(firstName) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(email=email, firstName=firstName, password=generate_password_hash(password1, method='scrypt'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))

    return render_template("sign_up.html", user=current_user)
