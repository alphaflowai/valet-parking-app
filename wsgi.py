# wsgi.py
import sys
import logging
from flask import Flask, jsonify, request

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)
logger = logging.getLogger(__name__)

try:
    from app import create_app, socketio
    logger.info("Successfully imported app modules")
except Exception as e:
    logger.error(f"Failed to import app modules: {str(e)}")
    raise

# Create application
try:
    app = create_app()
    logger.info("Successfully created Flask application")
except Exception as e:
    logger.error(f"Failed to create Flask application: {str(e)}")
    raise

@app.before_request
def log_request():
    logger.debug(f"Request URL: {request.url}")
    logger.debug(f"Request Method: {request.method}")
    logger.debug(f"Request Headers: {dict(request.headers)}")

@app.route('/', methods=['GET'])
def index():
    logger.info("Handling request to root endpoint")
    return jsonify({
        'status': 'ok',
        'message': 'Valet Parking API Server',
        'python_version': sys.version,
        'debug': app.debug
    })

@app.route('/health', methods=['GET'])
def health():
    logger.info("Handling request to health endpoint")
    return jsonify({
        'status': 'healthy',
        'service': 'valet-parking-app'
    })

@app.errorhandler(404)
def not_found(error):
    logger.error(f"404 Error: {request.url}")
    return jsonify({
        'error': 'Not found',
        'status': 404,
        'path': request.path
    }), 404

# Create WSGI application
try:
    wsgi = socketio.middleware(app)
    logger.info("Successfully created WSGI middleware")
except Exception as e:
    logger.error(f"Failed to create WSGI middleware: {str(e)}")
    raise

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000)