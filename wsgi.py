# Import monkey patch first - before ANY other imports
from monkey import *

import os
import sys
import logging
from flask import Flask
from eventlet import wsgi
from eventlet import greenio

# Set up logging before anything else
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
logger.info(f"Eventlet version: {eventlet.__version__}")

try:
    # Initialize Flask
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-key-123'),
        DEBUG=True,
        JSON_SORT_KEYS=False,  # Preserve JSON key order
        PROPAGATE_EXCEPTIONS=True,  # Show detailed errors
    )
    
    logger.info("Flask app initialized")

    # Initialize SocketIO with eventlet support
    from flask_socketio import SocketIO
    
    socketio = SocketIO(
        app,
        async_mode='eventlet',
        cors_allowed_origins="*",
        logger=True,
        engineio_logger=True,
        ping_timeout=60,
        ping_interval=25,
        manage_session=False,
        always_connect=True,
        async_handlers=True
    )
    
    logger.info("SocketIO initialized")

    @app.route('/health')
    def health():
        return {'status': 'healthy', 'eventlet': True}, 200

    @app.route('/')
    def home():
        return {'status': 'running', 'mode': 'eventlet'}, 200

    @socketio.on('connect')
    def test_connect():
        socketio.emit('connected', {'data': 'Connected'})

    logger.info("Routes configured")
    logger.info("Application setup complete")

except Exception as e:
    logger.error(f"Error during initialization: {str(e)}", exc_info=True)
    raise

# This is what Gunicorn uses
wsgi = app

if __name__ == '__main__':
    socketio.run(app, debug=True)
