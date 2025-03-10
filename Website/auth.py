from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user
from datetime import datetime
from .views import log_action


auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in!', category='info')
        return redirect(url_for('views.home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if not user.is_verified:
                flash('Your account is pending verification by the admin.', category='error')
            elif check_password_hash(user.password, password):
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
    logout_user()
    session.clear()
    response = redirect(url_for('views.welcome'))
    response.delete_cookie('session')
    response.delete_cookie('remember_token')
    return response

@auth.route('/sign_up_constituent', methods=['GET', 'POST'])
def sign_up_constituent():
    if request.method == 'POST':
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        email = request.form.get('email')
        address = request.form.get('address')
        birth_date = request.form.get('birth_date')
        birth_place = request.form.get('birth_place')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(email=email, firstName=first_name, lastName = last_name, address=address, birth_date=birth_date, birth_place=birth_place, password=generate_password_hash(password1, method='scrypt'), is_verified=True)
            
            db.session.add(new_user)
            db.session.commit()
            # ✅ Log the sign-up in the audit trail
            log_action(email, "Signed up as a Constituent")
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))

    return render_template("sign_up.html", user=current_user)

@auth.route('/sign_up_official', methods=['GET', 'POST'])
def sign_up_official():
    if request.method == 'POST':
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        email = request.form.get('email')
        address = request.form.get('address')
        birth_date = datetime.strptime(request.form.get('birth_date'), "%Y-%m-%d").date()  # Convert to date
        birth_place = request.form.get('birth_place')
        position = request.form.get('position')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(
                email=email,
                firstName=first_name,
                lastName=last_name,
                address=address,
                birth_date=birth_date,  # Now a date object
                birth_place=birth_place,
                position=position,
                password=generate_password_hash(password1, method='scrypt'),
                is_verified=False
            )

            db.session.add(new_user)
            db.session.commit()

             # ✅ Log the sign-up in the audit trail
            log_action(email, f"Signed up as an Official ({position}), pending verification")

            flash('Your account has been submitted for verification.', category='info')
            return redirect(url_for('auth.login'))

    return render_template("sign_up_official.html", user=current_user)

@auth.route('/sign_up_selection')
def sign_up_selection():
    return render_template("sign_up_selection.html", user=current_user)


