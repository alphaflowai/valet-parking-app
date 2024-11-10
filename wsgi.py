# Import monkey patch first - before ANY other imports
from monkey import *

import os
from flask import Flask
from flask_socketio import SocketIO
import eventlet.wsgi

# Initialize Flask without any imports that could trigger RLock creation
app = Flask(__name__.split('.')[0])
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-123')

# Initialize SocketIO after Flask but before any other imports
socketio = SocketIO(
    app, 
    async_mode='eventlet',
    message_queue=None,  # Disable message queue to avoid Redis/RabbitMQ dependencies
    cors_allowed_origins="*"
)

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

@app.route('/')
def home():
    return {'status': 'running'}, 200

# The WSGI application
wsgi = app

if __name__ == '__main__':
    socketio.run(app)
