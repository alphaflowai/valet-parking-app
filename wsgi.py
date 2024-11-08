import eventlet
eventlet.monkey_patch()

from app import create_app, socketio

app = create_app()
application = socketio.middleware(app)

if __name__ == '__main__':
    socketio.run(app) 