from flask import Flask, render_template, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from werkzeug.security import generate_password_hash
from flask_mail import Mail 
from itsdangerous import URLSafeTimedSerializer
 

 
import logging

# Database configuration 
DB_NAME = "test3" 
SECRET_KEY = 'hjshjhdjah kjshkjdhjs'  
ADMIN_EMAIL = "chikomot@africau.edu"  #  admin email

# Create Flask and database instances
app = Flask(__name__)  
 


logging.basicConfig(filename='trial.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s', 
                    datefmt='%d-%b-%y %H:%M:%S')


logging.debug("This is a test")
 
db = SQLAlchemy()

# Mail configuration
mail = Mail()

# Token serializer setup
serializer = URLSafeTimedSerializer(SECRET_KEY)

def create_app(): 

    # Configure Flask app
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://root:21022001@localhost/{DB_NAME}'  # Replace with actual database credentials

    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465  
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True 
    app.config['MAIL_USERNAME'] = ADMIN_EMAIL  # Replace with actual Gmail address
    app.config['MAIL_PASSWORD'] = "nlzv jfds wpqq csjr"   # Replace with actual Gmail app password
    app.config['MAIL_DEFAULT_SENDER'] = ('VARRS Support', ADMIN_EMAIL) 

    # Initialize extensions
    db.init_app(app) 
    mail.init_app(app)
    
    
    # Model import
    from .models import Guard

    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()

        # Create an initial user (modify as needed)
        if not Guard.query.filter_by(username='Supervisor').first():
            initial_user = Guard(
                username='Supervisor',
                password=generate_password_hash(
                    'RandomPassword123', method='scrypt', salt_length=16),
                email=ADMIN_EMAIL,
                supervisor = True,
                suspended = False
            )
            db.session.add(initial_user)
            db.session.commit()

    # Import and register Blueprints (organize routes)
    from .routes.auth import auth
    from .routes.system import system
    from .routes.client_routes import client_routes
    from .routes.home_routes import home_routes
    from .routes.vehicle_routes import vehicle_routes
    from .routes.other import help_routes, settings_routes
    from .routes.forgot import forgot
    from .routes.admin import accounts

    app.register_blueprint(home_routes, url_prefix='/')
    app.register_blueprint(vehicle_routes, url_prefix='/')
    app.register_blueprint(client_routes, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(system, url_prefix='/')
    app.register_blueprint(help_routes, url_prefix='/')
    app.register_blueprint(settings_routes, url_prefix='/')
    app.register_blueprint(accounts, url_prefix='/')
    app.register_blueprint(forgot, url_prefix='/')


    # Configure Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login' 
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(guard_id):
        return Guard.query.get(int(guard_id))
 
    return app
