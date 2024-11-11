# Setup eventlet first
import eventlet
eventlet.monkey_patch(all=True)

# Standard library imports
import os
import logging
import sys

# Flask imports
from flask import Flask, request
from flask_socketio import SocketIO

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def create_app():
    """Create Flask application."""
    app = Flask(__name__)
    
    # Configuration
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-key-123'),
        DEBUG=os.getenv('FLASK_ENV') == 'development',
        TESTING=False
    )
    
    # Initialize SocketIO
    socketio = SocketIO(
        app,
        async_mode='eventlet',
        cors_allowed_origins="*",
        manage_session=False,
        logger=True,
        engineio_logger=True
    )
    
    @app.route('/health')
    def health():
        """Health check endpoint."""
        logger.info("Health check requested")
        return {'status': 'healthy'}, 200
    
    @app.route('/')
    def home():
        """Root endpoint."""
        logger.info("Root endpoint requested")
        return {'status': 'running'}, 200
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        logger.info("Client connected")
        socketio.emit('connected', {'data': 'Connected'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        logger.info("Client disconnected")
    
    return app

# Create the application
app = create_app()

# WSGI application
wsgi = app

if __name__ == '__main__':
    logger.info("Starting development server")
    socketio = SocketIO(app)
    socketio.run(app, debug=True)
