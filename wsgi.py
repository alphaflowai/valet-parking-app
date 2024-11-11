# First, monkey patch before ANY imports
import eventlet
eventlet.monkey_patch()

# Flask imports
import os
from flask import Flask, current_app
from flask_socketio import SocketIO

# Create Flask app
app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv('SECRET_KEY', 'dev-key-123'),
    DEBUG=False
)

# Push an application context that will be used by Gunicorn
ctx = app.app_context()
ctx.push()

# Initialize SocketIO after app context is pushed
socketio = SocketIO(
    app,
    async_mode='eventlet',
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False
)

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

@app.route('/')
def home():
    return {'status': 'running'}, 200

# This is what Gunicorn uses
wsgi = app

# Don't remove the context
if __name__ == '__main__':
    socketio.run(app)
