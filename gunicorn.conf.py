import multiprocessing

# Basic server configuration
wsgi_app = 'wsgi:wsgi'
bind = '0.0.0.0:8000'
worker_class = 'eventlet'
workers = 1
threads = 1
timeout = 120
keepalive = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'warning'
capture_output = True
enable_stdio_inheritance = True

# Proxy settings
proxy_allow_ips = '*'
forwarded_allow_ips = '*'

# Application loading
preload_app = True
reload = False

# Hook functions for application context
def when_ready(server):
    """Called just after the server is started."""
    from wsgi import app
    with app.app_context():
        server.log.info("Application context ready")

def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Server is starting")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info("Pre-fork hook")

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    from wsgi import app
    with app.app_context():
        server.log.info("Worker ready with application context")

def worker_exit(server, worker):
    """Called just after a worker has been exited."""
    from wsgi import app
    with app.app_context():
        server.log.info("Worker exiting")