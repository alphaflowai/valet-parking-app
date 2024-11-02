from flask import (
    current_app, flash, jsonify, make_response, redirect, 
    render_template, request, session as flask_session, url_for
)
from flask_login import current_user, login_required
from flask_socketio import emit, join_room, leave_room
from flask_wtf.csrf import validate_csrf, generate_csrf
from wtforms import ValidationError
from datetime import datetime, timedelta

from app import db, socketio
from app.main.routes import bp
from app.main.forms import (
    CarDetailsForm, ConfirmRetrievalForm, ParkingSpaceForm, 
    SMSForm, TicketForm, UpdateParkingSpaceForm, UpdateProfileForm, DonationForm
)
from app.main.routes.auth import valet_required
from app.main.routes.utility import (
    get_available_spaces, complete_session, 
    get_est_time, generate_qr, parking_session, update_car_details, format_time_parked,
    update_session_status, get_time_parked, get_session_status, emit_parking_space_assigned, 
    emit_session_update, get_qr_code, get_qr_code_customer_portal, generate_payment_qr
)
from app.models import CarDetails, Session, ValetStation
from config import Config
from twilio.rest import Client
import traceback
import json
import os

# Load vehicle data
current_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(current_dir, '..', '..', 'static', 'data', 'vehicle_make_models.json')

try:
    with open(json_path, 'r') as f:
        vehicle_data = json.load(f)
except Exception as e:
    current_app.logger.error(f"Error loading vehicle data: {str(e)}")
    vehicle_data = {"colors": [], "makes": [], "models": {}}

@bp.route('/valet/park_car', methods=['GET', 'POST'])
@login_required
@valet_required
def valet_park_car():
    current_app.logger.info("Entering valet_park_car function")
    qr_code_url = None
    session_id = request.args.get('session_id')
    if session_id:
        session = Session.query.get_or_404(session_id)
        car_details = CarDetails.query.filter_by(session_id=session.id).first()
        current_step = 'car_details' if not car_details else 'parking'
        qr_code_url = get_qr_code(session.id) or generate_qr(session.id)
    else:
        session = None
        current_step = 'ticket'
        qr_code_url = None

    ticket_form = TicketForm()
    car_details_form = CarDetailsForm()

    if request.method == 'POST':
        current_app.logger.info(f"POST request received. Form data: {request.form}")
        if 'ticket_number' in request.form:
            if ticket_form.validate_on_submit():
                ticket_number = ticket_form.ticket_number.data
                existing_session = Session.query.filter_by(ticket_number=ticket_number).first()
                if existing_session:
                    flash('This Session has already been used.', 'error')
                    return redirect(url_for('main.valet_park_car'))
                if not session:
                    session = parking_session(ticket_number)
                    
                current_step = 'car_details'
                qr_code_url = generate_qr(session.id)
                flash('Please enter car details.', 'success')
                return render_template('valet/park_car.html',
                                       ticket_form=ticket_form,
                                       car_details_form=car_details_form,
                                       session=session,
                                       qr_code_url=qr_code_url,
                                       current_step=current_step)
        elif 'vehicle_type' in request.form:
            if car_details_form.validate_on_submit():
                if not session:
                    session = Session.query.get_or_404(request.form.get('session_id'))
                update_car_details(session.id, car_details_form)
                session.status = 'parking'
                db.session.commit()
                flash('Car details updated successfully. Car is now in parking status.', 'success')
                return redirect(url_for('main.valet_dashboard'))

    return render_template('valet/park_car.html', 
                           ticket_form=ticket_form,
                           car_details_form=car_details_form,
                           session=session,
                           qr_code_url=qr_code_url,
                           current_step=current_step)

@bp.route('/get_models')
def get_models():
    make = request.args.get('make', '')
    current_app.logger.info(f"Received request for models of make: {make}")
    models = vehicle_data['models'].get(make, [])
    current_app.logger.info(f"Returning models: {models}")
    return jsonify(models)

@bp.route('/api/autocomplete', methods=['GET'])
def autocomplete():
    field = request.args.get('field')
    term = request.args.get('term')
    if field in ['color', 'make', 'model']:
        results = CarDetails.query.filter(getattr(CarDetails, field).like(f"%{term}%")).distinct().limit(10).all()
        return jsonify([getattr(r, field) for r in results])
    return jsonify([])

from app.main.routes.utility import (
    get_available_spaces, complete_session, 
    get_est_time, generate_qr, parking_session, update_car_details, format_time_parked,
)



@bp.route('/valet/dashboard')
@login_required
@valet_required
def valet_dashboard():
    try:
        status = request.args.get('status', 'open')
        
        # Get all active sessions for this valet
        sessions = Session.query.filter_by(valet_id=current_user.id).all()
        
        # Get available spaces for each session that needs them
        available_spaces = {}
        if current_user.assigned_station and current_user.assigned_station.spaces:
            station_spaces = current_user.assigned_station.spaces.split(',')
            for session in sessions:
                if session.status == 'parking' or (session.status in ['parked', 'active'] and not session.parking_space):
                    # Get currently occupied spaces
                    occupied_spaces = Session.query.filter(
                        Session.status.in_(['parked', 'parking']),
                        Session.parking_space.isnot(None)
                    ).with_entities(Session.parking_space).all()
                    occupied_spaces = [space[0] for space in occupied_spaces]
                    
                    # Filter out occupied spaces
                    available_spaces[session.id] = [
                        space for space in station_spaces 
                        if space not in occupied_spaces
                    ]
        # Get today's date in EST timezone
        today = get_est_time().date()
        completed_today = sum(
            1 for session in sessions 
            if session.status == 'completed' 
            and session.end_time 
            and get_est_time(session.end_time).date() == today
        )
        active_sessions = Session.query.filter(
            Session.valet_id == current_user.id,
            Session.status.in_(['parking', 'parked', 'retrieving', 'returning', 'ready'])
        ).all()
        completed_sessions = Session.query.filter(
            Session.valet_id == current_user.id,
            Session.status == 'completed'
        ).order_by(Session.end_time.desc()).all()
        total_spaces = current_user.assigned_station.total_spaces if current_user.assigned_station else 0
        if current_user.assigned_station:
            total_spaces = len(current_user.assigned_station.spaces.split(','))
        return render_template('valet/dashboard.html',
                             sessions=sessions,
                             current_status=status,
                             completed_today=completed_today,
                             available_spaces=available_spaces,
                             total_spaces=total_spaces,
                             active_sessions=active_sessions,
                             completed_sessions=completed_sessions)
                             
    except Exception as e:
        current_app.logger.error(f"Error in valet_dashboard: {str(e)}")
        flash('An error occurred while loading the dashboard.', 'error')
        return redirect(url_for('main.index'))

@bp.route('/valet/update_status/<int:session_id>', methods=['POST'])
@login_required
@valet_required
def update_status(session_id):
    data = request.json
    if not data:
        return jsonify({'status': 'error', 'message': 'No JSON data received'}), 400
    
    new_status = data.get('status')
    if not new_status:
        return jsonify({'status': 'error', 'message': 'No status provided'}), 400
    
    session = Session.query.get_or_404(session_id)
    
    if new_status not in ['parked', 'retrieving', 'returning', 'ready', 'completed']:
        return jsonify({'status': 'error', 'message': 'Invalid status'}), 400
    
    session.status = new_status
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Status updated successfully'})

from app.main.routes.utility import get_est_time, format_time_parked

@bp.route('/valet/ticket_details/<int:session_id>', methods=['GET', 'POST'])
@login_required
@valet_required
def ticket_details(session_id):
    session = Session.query.get_or_404(session_id)
    if session.valet_id != current_user.id:
        flash('You do not have permission to view this ticket.', 'error')
        return redirect(url_for('main.valet_dashboard'))
    
    car_details = CarDetails.query.filter_by(session_id=session_id).first()
    car_details_form = CarDetailsForm(obj=car_details) if car_details else CarDetailsForm()
    sms_form = SMSForm()
    
    # Get the saved QR code from the database
    qr_code = get_qr_code_customer_portal(session_id)
    
    if request.method == 'POST':
        if 'update_car_details' in request.form and car_details_form.validate_on_submit():
            update_car_details(session_id, form=car_details_form)
            flash('Car details updated successfully.', 'success')
        elif 'send_sms' in request.form and sms_form.validate_on_submit():
            # Handle SMS sending here
            flash('SMS sent successfully.', 'success')
        return redirect(url_for('main.ticket_details', session_id=session_id))
    
    available_spaces = get_available_spaces(current_user.id)
    return render_template('valet/ticket_details.html', 
                           session=session, 
                           car_details_form=car_details_form,
                           sms_form=sms_form,
                           car_details=car_details,
                           qr_code=qr_code,
                           available_spaces=available_spaces,
                           get_est_time=get_est_time,
                           format_time_parked=format_time_parked)

from flask import jsonify, request, render_template, flash, redirect, url_for


@socketio.on('update_customer_status', namespace='/valet')
def handle_update_customer_status(data):
    session_id = data['session_id']
    status = data['status']
    session = Session.query.get(session_id)
    if session:
        session.status = status
        db.session.commit()
        socketio.emit('status_update', {
            'session_id': session.id,
            'status': status,
            'formatted_time_parked': format_time_parked(session)
        }, room=f'customer_{session.id}')
    else:
        current_app.logger.error(f"Session {session_id} not found")

@bp.route('/valet/assign_space/<int:session_id>', methods=['POST'])
@login_required
@valet_required
def valet_assign_space(session_id):
    try:
        session = Session.query.get_or_404(session_id)
        data = request.get_json()
        
        if not data:
            current_app.logger.error("No JSON data received")
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        parking_space = data.get('parking_space')
        if not parking_space:
            current_app.logger.error("No parking space provided")
            return jsonify({'success': False, 'message': 'No parking space provided'}), 400

        session.parking_space = parking_space
        session.status = 'parked'
        session.parked_time = get_est_time()
        db.session.commit()
        
        # Emit updates
        emit_session_update(session.id, 'parking_space_assigned', {
            'parking_space': session.parking_space,
            # 'message': f'Your car has been parked in space {session.parking_space}'
        })
        
        return jsonify({
            'success': True, 
            'parking_space': session.parking_space,
            'status': session.status
        })
    except Exception as e:
        current_app.logger.error(f"Error assigning parking space: {str(e)}\n{traceback.format_exc()}")
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/check_retrieving_status')
@login_required
@valet_required
def check_retrieving_status():
    last_check = session.get('last_retrieving_check', datetime.min)
    new_retrieving = Session.query.filter(
        Session.valet_id == current_user.id,
        Session.status == 'retrieving',
        Session.car_requested_time > last_check
    ).first() is not None
    
    session['last_retrieving_check'] = datetime.utcnow()
    return jsonify({'new_retrieving': new_retrieving})

@bp.route('/valet/session/<int:session_id>')
@login_required
@valet_required
def valet_session_details(session_id):
    session = Session.query.get_or_404(session_id)
    if session.valet_id != current_user.id:
        flash('You do not have permission to view this session.')
        return redirect(url_for('main.valet_dashboard', status='open'))
    car_details = CarDetails.query.filter_by(session_id=session_id).first()
    return render_template('valet/session_details.html', session=session, car_details=car_details, venmo_username=current_user.venmo_username, cashapp_username=current_user.cashapp_username)


def update_customer_portal(session_id):
    session = Session.query.get(session_id)
    if session:
        print(f"Customer portal updated for session {session_id}")
    else:
        print(f"Session {session_id} not found")

@bp.route('/valet/send_sms/<int:session_id>', methods=['POST'])
@login_required
@valet_required
def send_sms(session_id):
    session = Session.query.get_or_404(session_id)
    sms_form = SMSForm()
    
    if sms_form.validate_on_submit():
        phone_number = sms_form.phone_number.data
        
        if not phone_number:
            flash('Please provide a valid phone number.', 'error')
            return redirect(url_for('main.ticket_details', session_id=session_id))
        
        portal_url = url_for('main.customer_portal', session_id=session_id, _external=True)
        message = f"Thank you for using our valet service. Access your session information here: {portal_url}"
        
        try:
            client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=message,
                from_=Config.TWILIO_PHONE_NUMBER,
                to=phone_number
            )
            flash('SMS with customer portal link sent successfully.', 'success')
        except Exception as e:
            flash(f'Error sending SMS: {str(e)}', 'error')
        
    return redirect(url_for('main.ticket_details', session_id=session_id))




@socketio.on('connect', namespace='/valet')
def handle_valet_connect():
    if current_user.is_authenticated and current_user.role == 'valet':
        join_room(f'valet_{current_user.id}')
        print(f'Valet {current_user.username} connected')

@socketio.on('disconnect', namespace='/valet')
def handle_valet_disconnect():
    if current_user.is_authenticated and current_user.role == 'valet':
        leave_room(f'valet_{current_user.id}')
        print(f'Valet {current_user.username} disconnected')

@bp.route('/valet/pick_up_car/<int:session_id>', methods=['POST'])
@login_required
@valet_required
def valet_pick_up_car(session_id):
    try:
        session = Session.query.get_or_404(session_id)
        if current_user.id != session.valet_id:
            return jsonify({'status': 'error', 'message': 'You do not have permission to update this session.'}), 403
        
        if session.status != 'retrieving':
            return jsonify({'status': 'error', 'message': 'This car is not in a retrieving state.'}), 400

        session.status = 'returning'
        db.session.commit()
        
        socketio.emit('car_being_returned', {
            'session_id': session.id,
            'valet_name': current_user.full_name,
            'message': f"Your car is being brought to the valet stand by {current_user.full_name}.",
            'status': 'returning'
        }, room=f'customer_{session.id}', namespace='/customer')
        
        socketio.emit('update_valet_ui', {
            'session_id': session.id,
            'status': session.status
        }, room=f'valet_{session.valet_id}', namespace='/valet')
        
        return jsonify({'status': 'success', 'message': 'Car is being returned to the customer', 'new_status': 'returning'})
    except Exception as e:
        current_app.logger.error(f"Error in valet_pick_up_car: {str(e)}")
        return jsonify({'status': 'error', 'message': 'An error occurred while processing your request'}), 500


@socketio.on('car_being_retrieved', namespace='/valet')
def handle_car_being_retrieved(data):
    session_id = data['session_id']
    valet_name = data['valet_name']
    session = Session.query.get(session_id)
    if session:
        update_session_status(session_id, 'returning')
        socketio.emit('car_being_retrieved', {
            'session_id': session.id,
            'status': 'returning',
            'valet_name': valet_name,
            'formatted_time_parked': format_time_parked(session)
        }, room=f'customer_{session.id}', namespace='/customer')
        socketio.emit('update_valet_ui', {
            'session_id': session.id,
            'status': 'returning'
        }, room=f'valet_{session.valet_id}', namespace='/valet')
    else:
        current_app.logger.error(f"Session {session_id} not found")

@socketio.on('car_picked_up', namespace='/valet')
def handle_car_picked_up(data):
    session_id = data['session_id']
    session = Session.query.get(session_id)
    if session:
        update_session_status(session_id, 'returning')
        socketio.emit('car_picked_up', {
            'session_id': session.id,
            'status': 'returning',
            'formatted_time_parked': format_time_parked(session)
        }, room=f'customer_{session.id}', namespace='/customer')
        socketio.emit('update_valet_ui', {
            'session_id': session.id,
            'status': 'returning'
        }, room=f'valet_{session.valet_id}', namespace='/valet')
    else:
        current_app.logger.error(f"Session {session_id} not found")



@bp.route('/valet/alert_customer/<int:session_id>', methods=['POST'])
@login_required
@valet_required
def alert_customer(session_id):
    try:
        session = Session.query.get_or_404(session_id)
        message = f"Valet Attendant {current_user.full_name} is alerting you about your car."
        
        # Single socket emission
        socketio.emit('valet_alert', {
            'session_id': session.id,
            'ticket_number': session.ticket_number,
            'valet_name': current_user.full_name,
            'message': message
        }, room=f'customer_{session.id}', namespace='/customer')
        
        return jsonify({
            'status': 'success',
            'message': 'Customer has been notified'
        })
    except Exception as e:
        current_app.logger.error(f"Error in alert_customer: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/valet/car_ready/<int:session_id>', methods=['POST'])
@login_required
@valet_required
def valet_car_ready(session_id):
    try:
        session = Session.query.get_or_404(session_id)
        if session.status != 'returning':
            return jsonify({'status': 'error', 'message': 'Invalid session status for this action'}), 400

        session.status = 'ready'
        db.session.commit()

        emit_session_update(session.id, 'car_ready', {
            'message': 'Your car is ready for pickup'
        })

        return jsonify({'status': 'success', 'message': 'Car is ready for pickup'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error marking car as ready: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@socketio.on('join', namespace='/customer')
def on_join(data):
    session_id = data['session_id']
    join_room(f'customer_{session_id}')
    
@socketio.on('car_parked', namespace='/valet')
def handle_car_parked(data):
    session_id = data['session_id']
    parking_space = data['parking_space']
    status = data['status']
    session = Session.query.get(session_id)
    if session:
        session.status = status
        session.parking_space = parking_space
        db.session.commit()
        socketio.emit('status_update', {
            'session_id': session.id,
            'status': status,
            'parking_space': parking_space,
            'formatted_time_parked': format_time_parked(session)
        }, room=f'customer_{session.id}', namespace='/customer')
        socketio.emit('update_valet_ui', {
            'session_id': session.id,
            'status': status,
            'parking_space': parking_space
        }, room=f'valet_{session.valet_id}', namespace='/valet')
        return jsonify({'success': True, 'message': 'Car parked successfully'})
    return jsonify({'success': False, 'message': 'Session not found'})


@bp.route('/complete_session/<int:session_id>', methods=['POST'])
@login_required
@valet_required
def complete_session_route(session_id):
    try:
        current_app.logger.info(f"Attempting to complete session {session_id}")
        session = Session.query.get_or_404(session_id)
        
        if session.status not in ['ready', 'returning', 'parked', 'parking', 'retrieving']:
            current_app.logger.warning(f"Session {session_id} not ready for completion. Status: {session.status}")
            return jsonify({'status': 'error', 'message': f'Session is not ready for completion. Current status: {session.status}'}), 400

        complete_session(session)
        payment_qr = generate_payment_qr(session.id)
        
        # Send a single, complete update
        socketio.emit('session_update', {
            'session_id': session.id,
            'status': 'completed',
            'update_type': 'completed',
            'message': 'Thank you for using our service!',
            'payment_qr': payment_qr,
            'formatted_time_parked': format_time_parked(session),
            'donation_form_html': render_template('customer/donation_form.html', 
                                                session=session,
                                                donation_form=DonationForm()),
            'timestamp': datetime.utcnow().isoformat()
        }, room=f'customer_{session.id}', namespace='/customer')
        
        current_app.logger.info(f"Session {session_id} completed successfully")
        return jsonify({'status': 'success', 'message': 'Session completed successfully'})
    except Exception as e:
        current_app.logger.error(f"Error completing session {session_id}: {str(e)}")
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': 'An error occurred while completing the session'}), 500

@bp.route('/valet/retrieve_car/<int:session_id>', methods=['POST'])
@login_required
@valet_required
def valet_retrieve_car(session_id):
    try:
        session = Session.query.get_or_404(session_id)
        if current_user.id != session.valet_id:
            return jsonify({'status': 'error', 'message': 'You do not have permission to update this session.'}), 403
        
        if session.status != 'parked':
            return jsonify({'status': 'error', 'message': 'This car is not in a parked state.'}), 400

        session.status = 'retrieving'
        db.session.commit()
        
        socketio.emit('car_being_retrieved', {
            'session_id': session.id,
            'valet_name': current_user.full_name,
            'message': f"Your car is being retrieved by {current_user.full_name}.",
            'status': 'retrieving'
        }, room=f'customer_{session.id}', namespace='/customer')
        
        socketio.emit('update_valet_ui', {
            'session_id': session.id,
            'status': session.status
        }, room=f'valet_{session.valet_id}', namespace='/valet')
        
        return jsonify({'status': 'success', 'message': 'Car retrieval process started', 'new_status': 'retrieving'})
    except Exception as e:
        current_app.logger.error(f"Error in valet_retrieve_car: {str(e)}")
        return jsonify({'status': 'error', 'message': 'An error occurred while processing your request'}), 500

@bp.route('/update_profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    form = UpdateProfileForm(current_user.username, current_user.email)
    if request.method == 'POST' and form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.username = form.username.data
            current_user.email = form.email.data
            current_user.first_name = form.first_name.data
            current_user.last_name = form.last_name.data
            current_user.phone_number = form.phone_number.data
            current_user.venmo_username = form.venmo_username.data
            current_user.cashapp_username = form.cashapp_username.data
            
            if form.new_password.data:
                if form.new_password.data == form.confirm_password.data:
                    current_user.set_password(form.new_password.data)
                else:
                    flash('New passwords do not match.', 'error')
                    return render_template('user_profile.html', form=form)
            
            db.session.commit()
            flash('Your profile has been updated.', 'success')
        else:
            flash('Invalid current password.', 'error')

    # Always populate the form with current user data
    form.username.data = current_user.username
    form.email.data = current_user.email
    form.first_name.data = current_user.first_name
    form.last_name.data = current_user.last_name
    form.phone_number.data = current_user.phone_number
    form.venmo_username.data = current_user.venmo_username
    form.cashapp_username.data = current_user.cashapp_username

    # Clear password fields
    form.current_password.data = ''
    form.new_password.data = ''
    form.confirm_password.data = ''

    return render_template('user_profile.html', form=form)



























