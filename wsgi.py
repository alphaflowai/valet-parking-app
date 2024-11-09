# Import monkey patch first - before ANY other imports
from monkey import *

import os
from flask import Flask
from flask_socketio import SocketIO

# Initialize Flask without any config for now
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-123')

# Initialize SocketIO with minimal config
socketio = SocketIO(
    app,
    async_mode='eventlet',
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

@app.route('/')
def health():
    return {'status': 'healthy'}, 200

# This is what Gunicorn uses
wsgi = app

if __name__ == '__main__':
    socketio.run(app)