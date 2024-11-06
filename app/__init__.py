from flask import Flask, request, url_for, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO, join_room, leave_room
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from dotenv import load_dotenv
import ssl
import os
import stripe

# Configure SSL and load environment variables
ssl._create_default_https_context = ssl._create_unverified_context
load_dotenv()

# Initialize Flask extensions
db = SQLAlchemy()
login = LoginManager()
login.login_view = 'main.login'
migrate = Migrate()
socketio = SocketIO(cors_allowed_origins="*", ssl_context=None)
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)
mail = Mail()

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    if os.environ.get('FLASK_ENV') == 'production':
        app.config.from_object('config.ProductionConfig')
    else:
        app.config.from_object('config.DevelopmentConfig')
    
    # Initialize extensions with app context
    db.init_app(app)
    login.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")
    csrf.init_app(app)  # Ensure CSRF is initialized
    limiter.init_app(app)
    mail.init_app(app)
    
    # Register blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    # Error handlers
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error('Server Error: %s', error)
        return jsonify(error=str(error)), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f"Unhandled exception: {str(e)}")
        return jsonify(error=str(e)), 500

    return app




