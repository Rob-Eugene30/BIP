from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import os


db = SQLAlchemy()
migrate = Migrate()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    migrate.init_app(app, db)

    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), "Website", "static", "uploads")


    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # Import User and Note models here after app initialization to avoid circular import
    from .models import User, Note, Document, Comment, AuditTrail

    with app.app_context():
        db.create_all()

        # Create admin user if it doesn't exist
        admin_user = User.query.filter_by(email="admin@ebip.com").first()
        if not admin_user:
            hashed_password = generate_password_hash("adminpass", method="scrypt")
            admin_user = User(firstName="admin", email="admin@bip.com", password=hashed_password, is_admin=True)
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created with hashed password!")


    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # Ensure session cookies are not persistent
    # app.config['REMEMBER_COOKIE_DURATION'] = None  # Session cookie (deleted when browser closes)
    app.config['SESSION_COOKIE_SECURE'] = True  # Optional: Ensure cookies are only sent over HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Optional: Prevent JavaScript access to cookies
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # Refresh session on each request
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    # Flask-Admin setup
    # Customizing the Admin Panel View to restrict to admin users
    class AdminOnlyModelView(ModelView):
        def is_accessible(self):
            return current_user.is_authenticated and current_user.is_admin

        def inaccessible_callback(self, name, **kwargs):
            return "Access Denied! Only admins can view this page.", 403

    # Set up Admin Panel
    admin = Admin(app, name='Admin Panel', template_mode='bootstrap3')
    admin.add_view(AdminOnlyModelView(User, db.session))  # Add User model to the admin panel
    admin.add_view(AdminOnlyModelView(Note, db.session))  # Add Note model to the admin panel

    return app


def create_database(app):
    if not path.exists('website/' + DB_NAME):
        with app.app_context():
            db.create_all()
            print('Created Database!')
