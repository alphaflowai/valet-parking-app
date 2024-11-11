# wsgi.py
import eventlet
eventlet.monkey_patch(
    os=True,
    select=True,
    socket=True,
    thread=True,
    time=True
)

import os
from flask import Flask, jsonify

# Initialize Flask
app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/')
def home():
    return jsonify({'status': 'running'})

# WSGI application
wsgi = app

if __name__ == '__main__':
    app.run()
