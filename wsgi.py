# Import monkey patch first - before ANY other imports
from monkey import *

import os
import logging
from flask import Flask, request
from flask_socketio import SocketIO

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask without any config for now
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-123')
app.config['DEBUG'] = True

# Initialize SocketIO with minimal config
socketio = SocketIO(
    app,
    async_mode='eventlet',
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    manage_session=False
)

@app.route('/')
def health():
    logger.debug("Health check endpoint called")
    return {'status': 'healthy'}, 200

@socketio.on('connect')
def test_connect():
    logger.info("Client connected")
    socketio.emit('connected', {'data': 'Connected'})

@socketio.on('disconnect')
def test_disconnect():
    logger.info("Client disconnected")

# For debugging
@app.before_request
def log_request_info():
    logger.debug('Headers: %s', dict(request.headers))
    logger.debug('Body: %s', request.get_data())

# Create combined WSGI app
wsgi = socketio.middleware(app)

if __name__ == '__main__':
    socketio.run(app, debug=True)
