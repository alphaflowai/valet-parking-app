# Import monkey patch first - before ANY other imports
from monkey import *

import os
import signal
from flask import Flask, request
from flask_socketio import SocketIO

class Config:
    """Application configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-123')
    DEBUG = False
    TESTING = False
    CORS_HEADERS = 'Content-Type'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize SocketIO
    socketio = SocketIO(
        app, 
        async_mode='eventlet',
        cors_allowed_origins="*",
        manage_session=False,
        logger=False,
        engineio_logger=False
    )
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {
            'status': 'healthy',
            'version': os.getenv('BUILD_VERSION', 'development')
        }, 200

    # Basic routes
    @app.route('/')
    def home():
        return {
            'status': 'running',
            'environment': os.getenv('FLASK_ENV', 'production')
        }, 200
    
    # Graceful shutdown handler
    def shutdown_handler(signum, frame):
        socketio.stop()
    
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    # Socket.IO events
    @socketio.on('connect')
    def handle_connect():
        app.logger.info('Client connected')
    
    @socketio.on('disconnect')
    def handle_disconnect():
        app.logger.info('Client disconnected')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Not Found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal Server Error'}, 500
    
    return app

# Create application instance
app = create_app()

# WSGI application
wsgi = app

if __name__ == '__main__':
    socketio = SocketIO(app)
    socketio.run(app)
