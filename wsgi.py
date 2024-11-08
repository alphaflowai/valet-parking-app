# Monkey patch must happen before any other imports
import eventlet
eventlet.monkey_patch()

# Now we can safely import our application
from app import create_app, socketio
from engineio.async_drivers import eventlet as async_eventlet

app = create_app()

# Initialize Socket.IO with the correct configuration
socketio.init_app(app, 
                 async_mode='eventlet',
                 message_queue=None,
                 cors_allowed_origins="*",
                 ping_timeout=60,
                 ping_interval=25)

# Create an application context for the main thread
app_ctx = app.app_context()
app_ctx.push()

# This is what Gunicorn uses
application = app

if __name__ == '__main__':
    socketio.run(app)