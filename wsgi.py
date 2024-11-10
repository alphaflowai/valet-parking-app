# Import monkey patch first - before ANY other imports
from monkey import *

import os
import sys
import logging
from flask import Flask
from eventlet import wsgi
from eventlet import greenio
import eventlet.wsgi

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Initialize Flask first
app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv('SECRET_KEY', 'dev-key-123'),
    DEBUG=True,
    JSON_SORT_KEYS=False,
    PROPAGATE_EXCEPTIONS=True
)

# Create application context
ctx = app.app_context()
ctx.push()

try:
    logger.info("Flask app initialized")

    # Initialize SocketIO within app context
    from flask_socketio import SocketIO
    socketio = SocketIO(
        app,
        async_mode='eventlet',
        cors_allowed_origins="*",
        logger=True,
        engineio_logger=True,
        message_queue=None
    )
    
    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200

    @app.route('/')
    def home():
        return {'status': 'running'}, 200

    @socketio.on('connect')
    def test_connect():
        logger.info("Client connected")
        socketio.emit('connected', {'data': 'Connected'})

    @socketio.on('disconnect')
    def test_disconnect():
        logger.info("Client disconnected")

    logger.info("Routes configured")
    logger.info("Application setup complete")

except Exception as e:
    logger.error(f"Error during initialization: {str(e)}", exc_info=True)
    ctx.pop()
    raise

# Create WSGI app
wsgi = app

# Don't pop the context - let Gunicorn handle it
if __name__ == '__main__':
    socketio.run(app, debug=True)
