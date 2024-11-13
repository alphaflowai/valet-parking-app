# wsgi.py
import sys
import logging
from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_login import current_user
import os

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

# Correct template and static directories
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'templates')
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static')

logger.info(f"Template directory: {template_dir}")
logger.info(f"Static directory: {static_dir}")

@app.before_request
def log_request():
    logger.debug(f"Request URL: {request.url}")
    logger.debug(f"Request Method: {request.method}")
    logger.debug(f"Request Headers: {dict(request.headers)}")
    logger.debug(f"Template Dir Exists: {os.path.exists(template_dir)}")
    logger.debug(f"Templates Available: {os.listdir(template_dir) if os.path.exists(template_dir) else 'No templates'}")

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(static_dir, filename)

# Create WSGI application
wsgi = socketio.middleware(app)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000)