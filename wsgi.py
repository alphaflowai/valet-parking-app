# monkey.py - Must be imported first
import sys

# Remove any previously imported modules
for module in list(sys.modules.keys()):
    if module.startswith(('threading', 'socket', '_socket', 'select')):
        del sys.modules[module]

import eventlet
eventlet.monkey_patch(all=True, aggressive=True)

# Verify monkey patching
import threading
assert eventlet.patcher.is_monkey_patched(threading), "Threading not properly patched!"

# wsgi.py
from monkey import *

import os
import logging
from flask import Flask, jsonify

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/health')
def health():
    logger.info("Health check called")
    return jsonify({'status': 'healthy'})

@app.route('/')
def home():
    logger.info("Root endpoint called")
    return jsonify({'status': 'running'})

# WSGI application
wsgi = app

if __name__ == '__main__':
    app.run()
