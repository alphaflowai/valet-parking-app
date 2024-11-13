from flask import current_app, render_template, flash, redirect, url_for, abort, request, jsonify
from flask_login import current_user, login_required
from app import db, socketio
from app.main.routes import bp
from valet_parking_app.app.models import Session
from datetime import datetime
from flask_wtf import FlaskForm
from flask import render_template
from flask_socketio import emit, join_room

from flask_wtf.csrf import CSRFProtect

# Add this import
from app.main.routes.utility import get_est_time, format_time_parked, get_time_parked, emit_session_update

from app.main.forms import DonationForm

def customer_request_car(session_id):
    session = Session.query.get_or_404(session_id)
    current_app.logger.info(f"Session customer_id: {session.customer_id}, Current user id: {current_user.id if not current_user.is_anonymous else 'Anonymous'}")
    
    # Remove the login check, but keep a basic authorization check
    if session.status == 'completed':
        return jsonify({'status': 'error', 'message': 'This session has already been completed.'}), 400
    elif session.status == 'retrieving':
        return jsonify({'status': 'error', 'message': 'Your car is already being retrieved.'}), 400
    
    try:
        session.status = 'retrieving'
        session.car_requested_time = datetime.utcnow()
        db.session.commit()

        # Emit update to valet dashboard
        socketio.emit('car_request', {
            'session_id': session.id,
            'message': 'Customer has requested their car',
            'car_requested_time': session.car_requested_time.strftime('%I:%M %p'),
            'ticket_number': session.ticket_number,
            'parking_space': session.parking_space
        }, room=f'valet_{session.valet_id}', namespace='/valet')

        # Emit update to customer portal (without alert)
        emit_session_update(session.id, 'status_update', {
            'status': 'retrieving',
            'car_requested_time': session.car_requested_time.strftime('%I:%M %p')
        })

        return jsonify({
            'status': 'success',
            'message': 'Car request sent successfully',
            'car_requested_time': session.car_requested_time.strftime('%I:%M %p')
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error requesting car: {str(e)}")
        return jsonify({'status': 'error', 'message': 'An error occurred while processing your request.'}), 500

def test_websocket():
    return render_template('customer/websocket_test.html')

class RequestCarForm(FlaskForm):
    pass


@bp.route('/customer/portal/<int:session_id>')
def customer_portal(session_id):
    parking_session = Session.query.get_or_404(session_id)
    donation_form = DonationForm()
    est_start_time = get_est_time(parking_session.start_time)
    return render_template('customer/portal.html', 
                           session=parking_session, 
                           donation_form=donation_form, 
                           format_time_parked=format_time_parked,
                           est_start_time=est_start_time)

@bp.route('/customer/request_car/<int:session_id>', methods=['POST'])
def customer_request_car(session_id):
    session = Session.query.get_or_404(session_id)
    
    if session.status == 'completed':
        return jsonify({'status': 'error', 'message': 'This session has already been completed.'}), 400
    elif session.status == 'retrieving':
        return jsonify({'status': 'error', 'message': 'Your car is already being retrieved.'}), 400
    
    try:
        session.status = 'retrieving'
        session.car_requested_time = datetime.utcnow()
        db.session.commit()

        # Emit update to valet dashboard
        socketio.emit('car_request', {
            'session_id': session.id,
            'message': 'Customer has requested their car',
            'car_requested_time': session.car_requested_time.strftime('%I:%M %p'),
            'ticket_number': session.ticket_number,
            'parking_space': session.parking_space
        }, room=f'valet_{session.valet_id}', namespace='/valet')

        # Emit update to customer portal (without alert)
        emit_session_update(session.id, 'status_update', {
            'status': 'retrieving',
            'car_requested_time': session.car_requested_time.strftime('%I:%M %p')
        })

        return jsonify({
            'status': 'success',
            'message': 'Car request sent successfully',
            'car_requested_time': session.car_requested_time.strftime('%I:%M %p')
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error requesting car: {str(e)}")
        return jsonify({'status': 'error', 'message': 'An error occurred while processing your request.'}), 500

@socketio.on('connect', namespace='/customer')
def handle_customer_connect():
    if 'socketId' in request.args:
        old_sid = request.args['socketId']
        flask_socketio.join_room(old_sid)

@socketio.on('disconnect', namespace='/customer')
def customer_disconnect():
    print('Customer disconnected')

@socketio.on('join', namespace='/customer')
def customer_join(data):
    session_id = data['session_id']
    room = f'customer_{session_id}'
    join_room(room)
    current_app.logger.info(f'Customer joined room: {room}')

@socketio.on('valet_alert', namespace='/customer')
def handle_valet_alert(data):
    session_id = data['session_id']
    valet_name = data['valet_name']
    emit('valet_alert', {
        'session_id': session_id,
        'valet_name': valet_name,
        'message': f"Valet Attendant {valet_name} is picking up your car."
    }, room=f'customer_{session_id}')
    current_app.logger.info(f"Valet alert received for session {session_id}")

@bp.route('/customer/sessions')
def customer_sessions():
    active_sessions = Session.query.filter_by(customer_id=current_user.id, status='active').all()
    past_sessions = Session.query.filter_by(customer_id=current_user.id, status='completed').order_by(Session.end_time.desc()).limit(10).all()
    return render_template('customer/sessions.html', active_sessions=active_sessions, past_sessions=past_sessions)

@socketio.on('join', namespace='/customer')
def on_join(data):
    session_id = data['session_id']
    room = f'customer_{session_id}'
    join_room(room)
    print(f'Customer joined room: {room}')

@socketio.on('session_update', namespace='/customer')
def handle_session_update(data):
    session_id = data['session_id']
    update_type = data['update_type']
    current_app.logger.info(f"Received session_update event for session {session_id}: {update_type}")
    emit('session_update', data, room=f'customer_{session_id}')

@bp.route('/customer/process_donation/<int:session_id>', methods=['POST'])
@login_required
def process_donation(session_id):
    session = Session.query.get_or_404(session_id)
    form = DonationForm()
    if form.validate_on_submit():
        # Here you can add any backend processing if needed
        flash('Thank you for your donation!', 'success')
    else:
        flash('There was an error processing your donation. Please try again.', 'error')
    return redirect(url_for('main.customer_portal', session_id=session_id))

@bp.route('/customer/process_payment/<int:session_id>', methods=['GET', 'POST'])
def process_payment(session_id):
    parking_session = Session.query.get_or_404(session_id)
    form = DonationForm()

    if form.validate_on_submit():
        amount = form.amount.data
        payment_method = form.payment_method.data

        # Generate payment link based on the payment method
        if payment_method == 'venmo':
            payment_link = f"venmo://paycharge?txn=pay&recipients={parking_session.valet.venmo_username}&amount={amount}&note=Valet%20Service%20Donation"
        elif payment_method == 'cashapp':
            payment_link = f"https://cash.app/${parking_session.valet.cashapp_username}/{amount}"
        else:
            flash('Invalid payment method', 'error')
            return redirect(url_for('main.customer_portal', session_id=session_id))

        # Store payment info in Flask session
        flask_session['pending_payment'] = {
            'session_id': session_id,
            'amount': amount,
            'payment_method': payment_method
        }

        # Redirect to payment app
        return redirect(payment_link)

    return render_template('customer/donation_form.html', form=form, session=parking_session)

@bp.route('/customer/payment_callback')
def payment_callback():
    pending_payment = flask_session.pop('pending_payment', None)
    if not pending_payment:
        flash('No pending payment found', 'error')
        return redirect(url_for('main.customer_portal'))

    # Here you would typically verify the payment with the payment provider
    # For this example, we'll just assume the payment was successful

    session_id = pending_payment['session_id']
    amount = pending_payment['amount']
    payment_method = pending_payment['payment_method']

    # Update the session with payment info
    session = Session.query.get(session_id)
    session.donation_amount = amount
    session.payment_method = payment_method
    db.session.commit()

    flash('Thank you for your donation!', 'success')
    return redirect(url_for('main.customer_portal', session_id=session_id))

# Remove or update other socket event handlers to use this new centralized approach

@bp.route('/request_car/<int:session_id>', methods=['POST'])
def request_car(session_id):
    try:
        session = Session.query.get_or_404(session_id)
        if session.status not in ['parked', 'parking']:
            return jsonify({'status': 'error', 'message': 'Car is not available for retrieval'}), 400

        session.status = 'retrieving'
        db.session.commit()

        emit_session_update(session.id, 'car_requested', {
            'ticket_number': session.ticket_number,
            'parking_space': session.parking_space
        })

        return jsonify({'status': 'success', 'message': 'Car retrieval requested'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error requesting car: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500




