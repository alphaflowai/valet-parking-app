import eventlet
eventlet.monkey_patch()

from app import create_app, socketio

app = create_app()
socketio.init_app(app, async_mode='eventlet')
# Create WSGI middleware
application = socketio.get_wsgi_app(app)

if __name__ == '__main__':
    socketio.run(app) 