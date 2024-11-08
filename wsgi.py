# Monkey patch must happen before any other imports
import eventlet
eventlet.monkey_patch(all=True, socket=True, time=True, select=True, os=True)

# Now we can safely import our application
from app import create_app, socketio

app = create_app()

# Initialize Socket.IO with the correct configuration
socketio.init_app(app, 
                 async_mode='eventlet',
                 message_queue=None,
                 cors_allowed_origins="*",
                 ping_timeout=60,
                 ping_interval=25)

# This is what Gunicorn uses
application = app

if __name__ == '__main__':
    socketio.run(app)