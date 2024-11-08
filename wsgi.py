# Monkey patch must happen before any other imports
import eventlet
eventlet.monkey_patch(os=True, select=True, socket=True, thread=True, time=True)

# Now we can safely import our application
from app import create_app, socketio
from flask import request

app = create_app()

# Initialize Socket.IO with the correct configuration
socketio.init_app(app, 
                 async_mode='eventlet',
                 message_queue=None,
                 cors_allowed_origins="*",
                 ping_timeout=60,
                 ping_interval=25,
                 always_connect=True)

# Create an application context for the main thread
app_ctx = app.app_context()
app_ctx.push()

# This is what Gunicorn uses
application = socketio.middleware(app)

@socketio.on_error_default
def default_error_handler(e):
    app.logger.error(f'SocketIO Error: {str(e)}')

if __name__ == '__main__':
    socketio.run(app) 