# wsgi.py
from app import create_app, socketio

app = create_app()

# Add a health check endpoint
@app.route('/')
def home():
    return {
        'status': 'ok',
        'message': 'Flask server is running'
    }

@app.route('/health')
def health():
    return {
        'status': 'healthy',
        'service': 'valet-parking-app'
    }

wsgi = socketio.middleware(app)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000)