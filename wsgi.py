# Setup eventlet first
import eventlet
eventlet.monkey_patch(all=True)

import os
from flask import Flask
from flask_socketio import SocketIO

# Initialize Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-123')

# Initialize SocketIO
socketio = SocketIO(
    app, 
    async_mode='eventlet',
    cors_allowed_origins="*"
)

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

@app.route('/')
def home():
    return {'status': 'running'}, 200

# WSGI application
wsgi = app

if __name__ == '__main__':
    socketio.run(app)
