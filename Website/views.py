from flask import Blueprint, render_template

views = Blueprint('viewing', __name__) #Name can be anything

@views.route('/') #Decorator, points to function below
def home():
    return render_template("home.html")


