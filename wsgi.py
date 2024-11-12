# wsgi.py
import logging
from flask import Flask, request
from app import create_app, socketio

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)

app = create_app()

@app.before_request
def log_request_info():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.get_data())

@app.after_request
def log_response_info(response):
    app.logger.debug('Response: %s', response.get_data())
    return response

@app.route('/')
def home():
    app.logger.info('Accessed home route')
    return {
        'status': 'ok',
        'message': 'Flask server is running'
    }

@app.route('/health')
def health():
    app.logger.info('Health check requested')
    return {
        'status': 'healthy',
        'service': 'valet-parking-app'
    }

@app.errorhandler(404)
def not_found_error(error):
    app.logger.error('Page not found: %s', request.url)
    return {'error': 'Not Found', 'url': request.url}, 404

@app.errorhandler(Exception)
def internal_error(error):
    app.logger.exception('An error occurred')
    return {'error': str(error)}, 500

wsgi = socketio.middleware(app)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000)