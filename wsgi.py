# wsgi.py
from flask import Flask, jsonify
from app import create_app, socketio

app = create_app()

# Basic route handlers
@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'status': 'ok',
        'message': 'Valet Parking API Server'
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'valet-parking-app'
    })

@app.route('/api', methods=['GET'])
def api_root():
    return jsonify({
        'status': 'ok',
        'version': '1.0',
        'endpoints': ['/health', '/api']
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'status': 404}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error', 'status': 500}), 500

# Create WSGI application
wsgi = socketio.middleware(app)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000)