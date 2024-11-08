# Monkey patch must happen before any other imports
import eventlet
eventlet.monkey_patch(os=True, select=True, socket=True, thread=True, time=True)

# Now we can safely import our application
from app import create_app, socketio

app = create_app()
socketio.init_app(app, async_mode='eventlet', message_queue=None)

# This is what Gunicorn uses
application = socketio.middleware(app)

if __name__ == '__main__':
    socketio.run(app) 