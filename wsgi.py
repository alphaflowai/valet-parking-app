# wsgi.py
import sys
import logging
import os
from flask import Flask, jsonify, request, render_template, send_from_directory, url_for
from flask_login import current_user

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)
logger = logging.getLogger(__name__)

try:
    from app import create_app, socketio, db
    logger.info("Successfully imported app modules")
except Exception as e:
    logger.error(f"Failed to import app modules: {str(e)}")
    raise

# Create application
try:
    app = create_app()
    logger.info("Successfully created Flask application")
    
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
except Exception as e:
    logger.error(f"Failed to create Flask application: {str(e)}")
    raise

# Ensure directories exist
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'templates')
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static')

@app.before_request
def log_request():
    logger.debug(f"Request URL: {request.url}")
    logger.debug(f"Request Method: {request.method}")
    logger.debug(f"Request Headers: {dict(request.headers)}")
    logger.debug(f"Template Dir Exists: {os.path.exists(template_dir)}")
    logger.debug(f"Static Dir Exists: {os.path.exists(static_dir)}")

@app.route('/')
def landing():
    logger.info("Serving landing page")
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'valet-parking-app'
    })

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(static_dir, filename)

@app.errorhandler(404)
def not_found_error(error):
    logger.error(f"404 Error: {request.url}")
    if request.path.startswith('/api/'):
        return jsonify(error='Not found', path=request.path), 404
    return render_template('404.html'), 404

@app.context_processor
def utility_processor():
    def fix_url_for(endpoint, **values):
        try:
            return url_for(endpoint, **values)
        except Exception as e:
            logger.error(f"URL generation error for {endpoint}: {str(e)}")
            if endpoint == 'static':
                return f"/static/{values.get('filename', '')}"
            return '/'
    
    return dict(url_for=fix_url_for, current_user=current_user)

# Create WSGI application
wsgi = socketio.middleware(app)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000)