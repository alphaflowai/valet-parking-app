from flask import url_for, send_file, flash, redirect, jsonify, render_template, request, current_app, send_from_directory
from flask_login import login_required, current_user
from flask_wtf.csrf import validate_csrf
from wtforms import ValidationError
from app import db, socketio
from app.main.routes import bp
from valet_parking_app.app.models import Session, ValetStation, CarDetails, User
from app.main.forms import ParkingSpaceForm, ConfirmRetrievalForm, DonationForm
from app.main.routes.auth import valet_required
import io
from datetime import datetime, timedelta
import traceback
import qrcode
import io
import base64
import pytz
import os
import json


def get_est_time(time=None):
    est = pytz.timezone('US/Eastern')
    if time is None:
        current_time_est = datetime.now(est)
    else:
        current_time_est = time.astimezone(est) if time.tzinfo else est.localize(time)
    
    return current_time_est

def format_time_parked(session):
    try:
        if not session:
            return "N/A"
            
        if session.status == 'completed' and session.end_time:
            # Use end_time for completed sessions
            end_time = session.end_time
        else:
            # Use current time for active sessions
            end_time = datetime.utcnow()
            
        if not session.start_time:
            return "N/A"

        time_diff = end_time - session.start_time
        hours = time_diff.days * 24 + time_diff.seconds // 3600
        minutes = (time_diff.seconds % 3600) // 60

        formatted_time = {
            'hours': hours,
            'minutes': minutes
        }
        
        session.formatted_time_parked = json.dumps(formatted_time)
        return f"{hours} hours {minutes} minutes"
        
    except Exception as e:
        current_app.logger.error(f"Error formatting time for session {session.id}: {str(e)}")
        return "Time data unavailable"

def generate_qr(session_id):
    session = Session.query.get_or_404(session_id)
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url_for('main.customer_portal', session_id=session_id, _external=True))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    
    session.qr_code_customerPortal = img_str
    db.session.commit()
    
    emit_session_update(session.id, 'status_update', {
        'session_id': session.id,
        'status': session.status,
        'message': 'Parking Vehicle'
    })
    
    return f"data:image/png;base64,{img_str}"

def get_qr_code(session_id):
    session = Session.query.get_or_404(session_id)
    if session.qr_code_customerPortal:
        return f"data:image/png;base64,{session.qr_code_customerPortal}"
    return None

@bp.route('/generate_qr/<int:session_id>')
@login_required
def generate_qr_route(session_id):
    session = Session.query.get_or_404(session_id)
    if current_user.id != session.customer_id and current_user.role not in ['admin', 'manager', 'valet']:
        flash('You do not have permission to generate this QR code.', 'error')
        return redirect(url_for('main.index'))
    
    qr_code_url = generate_qr(session_id)
    qr_code_customer_portal = session.qr_code_customerPortal
    return send_file(io.BytesIO(base64.b64decode(qr_code_customer_portal.split(',')[1])), mimetype='image/png')

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated and current_user.role == 'valet':
        socketio.emit('join', {'room': f'valet_{current_user.id}'})



def get_available_spaces(ticket_number):
    session = Session.query.filter_by(ticket_number=ticket_number).first()
    if not session or not session.valet or not session.valet.assigned_station:
        return []
    
    all_spaces = session.valet.assigned_station.spaces.split(',') if session.valet.assigned_station.spaces else []
    occupied_spaces = [s.parking_space for s in Session.query.filter_by(valet_id=session.valet.id, status='parked').all() if s.parking_space]
    
    return [space for space in all_spaces if space not in occupied_spaces]

def complete_session(session):
    try:
        current_app.logger.info(f"Starting to complete session {session.id}")
        
        current_app.logger.info(f"Current session status: {session.status}")
        session.status = 'completed'
        
        current_app.logger.info(f"Setting end time for session {session.id}")
        session.end_time = datetime.utcnow()
        
        current_app.logger.info(f"Storing closed parking space: {session.parking_space}")
        session.closed_parking_space = session.parking_space
        
        current_app.logger.info("Clearing current parking space")
        session.parking_space = None
        
        current_app.logger.info("Committing changes to database")
        db.session.commit()
        
        current_app.logger.info(f"Emitting session update for completed session {session.id}")
        emit_session_update(session.id, 'completed', {
            'message': 'Session completed',
            'formatted_time_parked': format_time_parked(session)
        })
        
        current_app.logger.info("Clearing session from flask_session")
        from flask import session as flask_session
        flask_session.pop('current_session_id', None)
        
        current_app.logger.info(f"Session {session.id} completed successfully")
    except Exception as e:
        current_app.logger.error(f"Error in complete_session for session {session.id}: {str(e)}")
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        db.session.rollback()
        raise

def update_session_status(session_id, new_status):
    """
    Update session status and emit update to all connected clients
    """
    try:
        session = Session.query.get_or_404(session_id)
        valid_statuses = ['parking', 'parked', 'retrieving', 'returning', 'ready', 'completed']
        
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}")
        
        old_status = session.status
        session.status = new_status
        
        if new_status == 'completed':
            session.end_time = datetime.utcnow()
            session.closed_parking_space = session.parking_space
            session.parking_space = None
        
        db.session.commit()

        emit_session_update(session.id, 'status_update', {
            'previous_status': old_status,
            'message': f'Status updated to {new_status}'
        })

        return session

    except Exception as e:
        current_app.logger.error(f"Error updating session status: {str(e)}")
        db.session.rollback()
        raise

def get_session_status(session_id):
    session = Session.query.get_or_404(session_id)
    return {
        'status': session.status,
        'parking_space': session.parking_space,
        'formatted_time_parked': format_time_parked(session),
        'car_requested_time': session.car_requested_time.strftime('%I:%M %p') if session.car_requested_time else None
    }
    
@bp.route('/get_time_parked/<int:session_id>')
def get_time_parked(session_id):
    try:
        session = Session.query.get_or_404(session_id)
        formatted_time = format_time_parked(session)
        return jsonify({
            'time_parked': formatted_time,
            'success': True
        })
    except Exception as e:
        current_app.logger.error(f"Error getting time parked: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get time parked'
        }), 500

@bp.route('/get_session_status/<int:session_id>')
def get_session_status(session_id):
    session = Session.query.get_or_404(session_id)
    return jsonify({
        'status': session.status,
        'formatted_time_parked': format_time_parked(session)
    })

def emit_parking_space_assigned(session_id, parking_space):
    current_app.logger.info(f"Emitting parking_space_assigned for session {session_id}") # Tracer
    session = Session.query.get(session_id)
    status_data = {
        'session_id': session.id,
        'status': 'parked',
        'parking_space': parking_space,
        'formatted_time_parked': format_time_parked(session)
    }
    socketio.emit('parking_space_assigned', status_data, room=f'customer_{session.id}', namespace='/customer')
    socketio.emit('status_update', status_data, room=f'customer_{session.id}', namespace='/customer')
    current_app.logger.info(f"Emitted parking_space_assigned and status_update for session {session_id}") # Tracer

@bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, 'static/assets'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

def emit_session_update(session_id, update_type, additional_data=None):
    try:
        session = Session.query.get(session_id)
        if not session:
            current_app.logger.error(f"Session {session_id} not found")
            return

        data = {
            'session_id': session_id,
            'status': session.status,
            'update_type': update_type,
            'timestamp': datetime.utcnow().isoformat(),
            'time_parked': format_time_parked(session)
        }

        if additional_data:
            data.update(additional_data)

        # Emit to both valet and customer namespaces
        socketio.emit('session_update', data, 
                     room=f'customer_{session_id}', 
                     namespace='/customer')
        
        socketio.emit('session_update', data, 
                     room=f'valet_{session.valet_id}', 
                     namespace='/valet')

    except Exception as e:
        current_app.logger.error(f"Error in emit_session_update: {str(e)}")
        current_app.logger.error(traceback.format_exc())

def get_button_action(status):
    actions = {
        'parked': 'retrieve-car',
        'retrieving': 'pick-up-car',
        'returning': 'car-ready',
        'ready': 'complete-session'
    }
    return actions.get(status, '')

def get_button_text(status):
    texts = {
        'parked': 'Retrieve Car',
        'retrieving': 'Pick up Car',
        'returning': 'Car is Ready',
        'ready': 'Complete Session'
    }
    return texts.get(status, '')

def get_button_icon(status):
    icons = {
        'parked': 'fa-car',
        'retrieving': 'fa-walking',
        'returning': 'fa-check',
        'ready': 'fa-flag-checkered'
    }
    return icons.get(status, '')

def get_qr_code_customer_portal(session_id):
    session = Session.query.get_or_404(session_id)
    if session.qr_code_customerPortal:
        return f"data:image/png;base64,{session.qr_code_customerPortal}"
    else:
        # Generate QR code with the correct URL
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        portal_url = url_for('main.customer_portal', session_id=session_id, _external=True)
        current_app.logger.info(f"Generating QR code for URL: {portal_url}")  # Add logging
        qr.add_data(portal_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = io.BytesIO()
        img.save(buffered)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Save the generated QR code to the database
        session.qr_code_customerPortal = img_str
        db.session.commit()
        
        return f"data:image/png;base64,{img_str}"

def parking_session(ticket_number):
    existing_session = Session.query.filter_by(ticket_number=ticket_number).first()
    if existing_session:
        raise ValueError('This ticket number has already been used.')
    
    session = Session(
        ticket_number=ticket_number,
        valet_id=current_user.id,
        status='parking',
        start_time=datetime.utcnow()
    )
    db.session.add(session)
    db.session.commit()
    return session

# Add this function if it's not already present
def update_car_details(session_id, form):
    session = Session.query.get(session_id)
    if not session:
        raise ValueError(f"Session with id {session_id} not found")
    
    car_details = CarDetails.query.filter_by(session_id=session_id).first()
    if not car_details:
        car_details = CarDetails(session_id=session_id)
        db.session.add(car_details)
    
    car_details.vehicle_type = form.vehicle_type.data
    car_details.color = form.color.data
    car_details.make = form.make.data
    car_details.model = form.model.data
    car_details.license_plate = form.license_plate.data
    
    db.session.commit()

def generate_payment_qr(session_id):
    payment_url = url_for('main.process_payment', session_id=session_id, _external=True)
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(payment_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"


















