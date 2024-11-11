# Monkey patch first
import eventlet
eventlet.monkey_patch()

import os
from flask import Flask, request

app = Flask(__name__)

@app.before_request
def before_request():
    if 'X-Forwarded-Proto' in request.headers:
        if request.headers['X-Forwarded-Proto'] != 'https':
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)

@app.route('/')
def home():
    return {
        'status': 'running',
        'version': '1.0',
        'endpoints': {
            'health': '/health',
            'api': '/api'
        }
    }

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

@app.route('/api')
def api():
    return {
        'service': 'Valet Parking API',
        'status': 'active'
    }

wsgi = app

if __name__ == '__main__':
    app.run()
