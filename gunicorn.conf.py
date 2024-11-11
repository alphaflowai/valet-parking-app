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

def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Server is starting")

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker started")