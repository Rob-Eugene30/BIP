from flask import Flask

def create_app():
    app = Flask(__name__) #name = name of the file
    app.config['SECRET_KEY'] = 'randomshit' #Encrypts the data/cookies in the session

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix ='/')
    app.register_blueprint(auth, url_prefix ='/') #location where it goes

    return app




