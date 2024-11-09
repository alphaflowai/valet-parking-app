# Import monkey patch first - before ANY other imports
from monkey import *

import os
from flask import Flask
from flask_socketio import SocketIO
from engineio.async_drivers import eventlet

# Initialize Flask without any config for now
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-123')

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
    return {'status': 'healthy'}, 200

@socketio.on('connect')
def test_connect():
    print('Client connected')
    socketio.emit('connected', {'data': 'Connected'})

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

# Create the WSGI application
wsgi = socketio.wsgi_app

if __name__ == '__main__':
    socketio.run(app)