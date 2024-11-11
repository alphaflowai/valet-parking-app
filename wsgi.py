# Monkey patch first
import eventlet
eventlet.monkey_patch()

import os
import logging
from flask import Flask, jsonify

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['DEBUG'] = True

@app.route('/health')
def health():
    logger.info("Health check called")
    return jsonify({'status': 'healthy'})

@app.route('/')
def home():
    logger.info("Root endpoint called")
    return jsonify({'status': 'running'})

@app.route('/api')
def api():
    logger.info("API endpoint called")
    return jsonify({
        'service': 'Valet Parking API',
        'status': 'active'
    })

# This is what Gunicorn uses
wsgi = app

if __name__ == '__main__':
    app.run()
