# wsgi.py
from app import create_app, socketio

# Create the Flask application instance
app = create_app()

# Create the WSGI interface
wsgi = socketio.middleware(app)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000)