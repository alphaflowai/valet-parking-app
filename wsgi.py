import eventlet
eventlet.monkey_patch()

from app import create_app, socketio

app = create_app()
socketio.init_app(app)
application = app.wsgi_app

if __name__ == '__main__':
    socketio.run(app) 