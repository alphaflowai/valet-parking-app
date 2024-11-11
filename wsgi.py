# Import and verify monkey patching first
from monkey import *

import os
import logging
from flask import Flask
from flask_socketio import SocketIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # Basic configuration
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-key-123'),
        DEBUG=False,
        TESTING=False,
        CORS_HEADERS='Content-Type'
    )
    
    # Initialize SocketIO
    socketio = SocketIO(
        app, 
        async_mode='eventlet',
        cors_allowed_origins="*",
        manage_session=False,
        logger=False,
        engineio_logger=False
    )
    
    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200

    @app.route('/')
    def home():
        return {'status': 'running'}, 200
    
    @socketio.on('connect')
    def handle_connect():
        logger.info('Client connected')
    
    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info('Client disconnected')
    
    return app

# Create app
app = create_app()

# WSGI application
wsgi = app
