# Monkey patch first
import eventlet
eventlet.monkey_patch()

import os
from flask import Flask

# Create basic Flask app
app = Flask(__name__)

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

@app.route('/')
def home():
    return {'status': 'running'}, 200

# WSGI app
wsgi = app

if __name__ == '__main__':
    app.run()
