from app import socketio
from flask_login import current_user

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated and current_user.role == 'valet':
        socketio.emit('join', {'room': f'valet_{current_user.id}'})