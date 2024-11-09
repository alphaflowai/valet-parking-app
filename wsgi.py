# Import monkey patch first - before ANY other imports
from monkey import *

import os
import sys
import logging
from flask import Flask, request

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Log startup information
logger.info(f"Python version: {sys.version}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"PYTHONPATH: {os.getenv('PYTHONPATH')}")

try:
    # Initialize Flask
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-123')
    app.config['DEBUG'] = True
    
    logger.info("Flask app initialized")

    # Initialize SocketIO after successful Flask init
    from flask_socketio import SocketIO
    socketio = SocketIO(
        app,
        async_mode='eventlet',
        cors_allowed_origins="*",
        logger=True,
        engineio_logger=True
    )
    
    logger.info("SocketIO initialized")

    @app.route('/health')
    def health():
        logger.info("Health check endpoint called")
        return {'status': 'healthy'}, 200

    @app.route('/')
    def home():
        logger.info("Root endpoint called")
        return {'status': 'running'}, 200

    @socketio.on('connect')
    def test_connect():
        logger.info("Client connected")
        socketio.emit('connected', {'data': 'Connected'})

    @socketio.on('disconnect')
    def test_disconnect():
        logger.info("Client disconnected")

    # Log successful setup
    logger.info("Application setup complete")

except Exception as e:
    logger.error(f"Error during initialization: {str(e)}", exc_info=True)
    raise

# This is what Gunicorn uses
wsgi = app

if __name__ == '__main__':
    socketio.run(app, debug=True)
