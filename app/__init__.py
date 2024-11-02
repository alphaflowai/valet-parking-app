from flask import Flask, request, url_for, redirect, jsonify  # Add 'jsonify' here
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO, join_room, leave_room
from config import Config
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import ssl
import os
from sqlalchemy import func 
from flask_mail import Mail  # Add this import
import stripe


ssl._create_default_https_context = ssl._create_unverified_context

load_dotenv()

db = SQLAlchemy()
login = LoginManager()
login.login_view = 'main.login'
migrate = Migrate()
socketio = SocketIO(cors_allowed_origins="*", ssl_context=None)
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)
mail = Mail()  # Add this line

def create_app():
    app = Flask(__name__)
    
    # Load the appropriate configuration
    if os.environ.get('FLASK_ENV') == 'production':
        app.config.from_object('config.production.ProductionConfig')
    else:
        app.config.from_object('config.development.DevelopmentConfig')
    
    # Initialize extensions
    db.init_app(app)
    login.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")
    limiter.init_app(app)
    mail.init_app(app)  # Add this line
    
    # Move the CLI import and initialization here, after db is fully set up
    from app import cli
    cli.init_app(app)
    
    from app.main.routes import bp as main_bp
    app.register_blueprint(main_bp)  
    
    from app.cli import create_admin
    app.cli.add_command(create_admin)
    
    @socketio.on('connect', namespace='/customer')
    def handle_connect():
        print('Client connected')

    @socketio.on('join', namespace='/customer')
    def on_join(data):
        if 'session_id' not in data:
            print("Error: session_id not provided in join event")
            return
        
        session_id = data['session_id']
        room = f'customer_{session_id}'
        join_room(room)
        print(f'Customer joined room: {room}')
    
    @socketio.on('leave', namespace='/customer')
    def on_leave(data):
        if 'room' in data:
            room = data['room']
            leave_room(room)
            print(f"User left room: {room}")
        else:
            print("No room specified in leave request")
            
    @app.route('/debug/routes')
    def list_routes():
        output = []
        for rule in app.url_map.iter_rules():
            options = {}
            for arg in rule.arguments:
                options[arg] = f"[{arg}]"
            methods = ','.join(rule.methods)
            url = url_for(rule.endpoint, **options)
            line = f"{rule.endpoint:50s} {methods:20s} {url}"
            output.append(line)
        
        return "<br>".join(output)

    @app.before_request
    def log_request_info():
        app.logger.debug('Headers: %s', request.headers)
        app.logger.debug('Body: %s', request.get_data())

    @app.after_request
    def log_response_info(response):
        app.logger.debug('Response Status: %s', response.status)
        if response.direct_passthrough:
            app.logger.debug('Response: Direct passthrough')
        else:
            app.logger.debug('Response: %s', response.get_data())
        return response

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error('Server Error: %s', (error))
        return jsonify(error=str(error)), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        # Log the error
        app.logger.error(f"Unhandled exception: {str(e)}")
        # Return JSON instead of HTML for HTTP errors
        return jsonify(error=str(e)), 500

    return app




