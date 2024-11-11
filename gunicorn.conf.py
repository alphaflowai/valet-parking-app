# Basic server configuration
bind = '0.0.0.0:8000'
worker_class = 'eventlet'
workers = 1
threads = 1

# Worker settings
worker_connections = 1000
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 100

# Logging
errorlog = '-'
accesslog = '-'
loglevel = 'debug'
capture_output = True
enable_stdio_inheritance = True

# Server settings
daemon = False
preload_app = True
reload = False

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    # Ensure eventlet is properly configured
    import eventlet
    eventlet.monkey_patch(all=True)
    server.log.info("Eventlet monkey patching completed")

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker {worker.pid} initialized")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT"""
    worker.log.info("Worker received interrupt signal")

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal"""
    worker.log.info("Worker received abort signal")

def worker_exit(server, worker):
    """Called just after a worker has been exited"""
    server.log.info(f"Worker {worker.pid} exited")