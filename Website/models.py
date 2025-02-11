from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    firstName = db.Column(db.String(150), nullable=False)  # For first name
    password = db.Column(db.String(150), nullable=False)  # For storing password hash
    is_admin = db.Column(db.Boolean, default=False)  # Optional: for admin flag
    #password_confirm = db.Column(db.String(150), nullable=False)  # Added for password confirmation (for form logic, not stored in DB)

    def __repr__(self):
        return f'<User {self.email}>'
