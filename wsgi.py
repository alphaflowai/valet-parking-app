# Import monkey patch first - before ANY other imports
from monkey import *

import os
import logging
from flask import Flask, request
from flask_socketio import SocketIO

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-123')
app.config['DEBUG'] = True

# Initialize SocketIO
socketio = SocketIO(
    app,
    async_mode='eventlet',
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

@app.route('/')
def health():
    logger.info("Health check endpoint called")
    return {'status': 'healthy'}, 200

@socketio.on('connect')
def test_connect():
    logger.info("Client connected")
    socketio.emit('connected', {'data': 'Connected'})

@socketio.on('disconnect')
def test_disconnect():
    logger.info("Client disconnected")

# This is what Gunicorn uses
wsgi = app

if __name__ == '__main__':
    socketio.run(app, debug=True)
