wsgi_app = 'wsgi:application'
bind = '0.0.0.0:8000'
worker_class = 'eventlet'
workers = 1
threads = 1
timeout = 30
keepalive = 2 