# wsgi.py
import sys
import logging
from flask import Flask, jsonify, request, render_template, send_from_directory
import os

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

# Ensure the template directory exists
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'templates')
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static')

@app.before_request
def log_request():
    logger.debug(f"Request URL: {request.url}")
    logger.debug(f"Request Method: {request.method}")
    logger.debug(f"Request Headers: {dict(request.headers)}")
    logger.debug(f"Template Dir Exists: {os.path.exists(template_dir)}")

# After imports and app creation, but before any routes
try:
    from app.main.routes import bp as main_bp
    from app.auth.routes import bp as auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    logger.info("Successfully registered blueprints")
except Exception as e:
    logger.error(f"Failed to register blueprints: {str(e)}")
    raise

# Then define routes
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(static_dir, filename)

@app.route('/health', methods=['GET'])
def health():
    logger.info("Handling request to health endpoint")
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

@app.errorhandler(404)
def not_found(error):
    logger.error(f"404 Error: {request.url}")
    if request.headers.get('Accept', '').find('application/json') != -1:
        return jsonify({
            'error': 'Not found',
            'status': 404,
            'path': request.path
        }), 404
    return render_template('404.html'), 404

# Create WSGI application
try:
    wsgi = socketio.middleware(app)
    logger.info("Successfully created WSGI middleware")
except Exception as e:
    logger.error(f"Failed to create WSGI middleware: {str(e)}")
    raise

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000)