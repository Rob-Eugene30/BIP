from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from datetime import datetime


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
    
class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)  # Stores the file path
    uploaded_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    user = db.relationship('User', backref='comments')
    document = db.relationship('Document', backref='comments')

class AuditTrail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_email = db.Column(db.String(150))
    action = db.Column(db.String(500))

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)  # Title of the announcement
    content = db.Column(db.Text, nullable=False)  # Content of the announcement
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())  # Timestamp
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # User who created the announcement

    user = db.relationship('User', backref='announcements')  # Relationship to User