# Import monkey patch first - before ANY other imports
from monkey import *

import os
import logging
from flask import Flask, current_app
from flask_socketio import SocketIO
import eventlet.wsgi

# Set up logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def create_app():
    # Initialize Flask
    app = Flask(__name__.split('.')[0])
    
    # Basic configuration
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-key-123'),
        DEBUG=False,
        TESTING=False,
        PRESERVE_CONTEXT_ON_EXCEPTION=True
    )
    
    # Push application context
    ctx = app.app_context()
    ctx.push()
    
    try:
        # Initialize SocketIO within context
        socketio = SocketIO(
            app, 
            async_mode='eventlet',
            message_queue=None,
            cors_allowed_origins="*"
        )
        
        @app.route('/health')
        def health():
            return {'status': 'healthy'}, 200

        @app.route('/')
        def home():
            return {'status': 'running'}, 200
            
        @socketio.on('connect')
        def handle_connect():
            logger.info('Client connected')
            
        @socketio.on('disconnect')
        def handle_disconnect():
            logger.info('Client disconnected')
            
        return app
        
    except Exception as e:
        logger.error(f"Error during app initialization: {e}")
        ctx.pop()
        raise

# Create the application with context
app = create_app()

# The WSGI application
wsgi = app

if __name__ == '__main__':
    socketio = SocketIO(app)
    socketio.run(app)
