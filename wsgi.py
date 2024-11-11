# Monkey patch first
import eventlet
eventlet.monkey_patch()

import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'version': '1.0'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/api')
def api():
    return jsonify({
        'service': 'Valet Parking API',
        'status': 'active'
    })

# This is what Gunicorn uses
wsgi = app

if __name__ == '__main__':
    app.run()
