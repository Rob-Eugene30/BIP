from flask import Blueprint, render_template, request, flash

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET','POST' ])
def login():
    return render_template("login.html")

@auth.route('/logout')
def logout():
    return "<p>Why'd you press that??? NERD!</p>"

@auth.route('/signin', methods=['GET','POST'])
def signin():
    if request.method=='POST':
        email = request.form.get('email')
        firstName = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        if len(email) < 4:
            flash('Email must have more than 4 characters.', category='error')
        elif len(firstName) < 2:
            flash('First Name must have more than 2 characters.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 3:
            flash('Password is too short.', category='error')
        else:
            flash('Account Created!', category='success')
            #Add user to the database

    return render_template("signin.html")