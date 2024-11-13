from flask import Blueprint, jsonify, request, current_app, url_for
from flask_login import login_required, current_user
from valet_parking_app.app.models import StationManager, ValetStation, ValetAttendant
from app.extensions import db, stripe

bp = Blueprint('stations', __name__)

@bp.route('/api/stations/create', methods=['POST'])
@login_required
def create_station():
    try:
        # Verify user is a station manager
        manager = StationManager.query.filter_by(user_id=current_user.id).first()
        if not manager:
            manager = StationManager(user_id=current_user.id)
            db.session.add(manager)
            db.session.commit()

        # Create Stripe subscription
        subscription = stripe.Subscription.create(
            customer=current_user.stripe_customer_id,
            items=[{'price': current_app.config['STATION_PRICE_ID']}],
            payment_behavior='default_incomplete',
            expand=['latest_invoice.payment_intent']
        )

        # Create station
        station = ValetStation(
            name=request.form.get('name'),
            location=request.form.get('location'),
            manager_id=manager.id
        )
        db.session.add(station)
        db.session.commit()

        return jsonify({
            'success': True,
            'station_id': station.id,
            'payment_url': subscription.latest_invoice.payment_intent.client_secret
        })

    except Exception as e:
        current_app.logger.error(f"Error creating station: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 400

@bp.route('/api/stations/<int:station_id>', methods=['GET'])
@login_required
def get_station(station_id):
    station = ValetStation.query.get_or_404(station_id)
    if not can_manage_station(current_user, station):
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({
        'id': station.id,
        'name': station.name,
        'location': station.location,
        'status': station.status,
        'spaces': station.space_usage_stats,
        'completed_parkings': station.completed_parkings,
        'valets': [{'id': v.id, 'name': v.user.name} for v in station.valets],
        'active_sessions': len([s for s in station.sessions if s.status != 'completed'])
    })

@bp.route('/api/stations/<int:station_id>/valets', methods=['POST'])
@login_required
def add_valet(station_id):
    station = ValetStation.query.get_or_404(station_id)
    if not can_manage_station(current_user, station):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        # Create user account for valet
        valet_user = User(
            email=request.form.get('email'),
            name=request.form.get('name'),
            role='valet'
        )
        valet_user.set_password(request.form.get('password'))
        db.session.add(valet_user)
        
        # Create valet attendant record
        valet = ValetAttendant(
            user_id=valet_user.id,
            station_id=station_id
        )
        db.session.add(valet)
        db.session.commit()

        return jsonify({
            'success': True,
            'valet_id': valet.id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@bp.route('/api/create-portal-session', methods=['POST'])
@login_required
def create_portal_session():
    try:
        # Create Stripe Portal session
        session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=url_for('main.manage_stations', _external=True),
        )
        return jsonify({'url': session.url})
    except Exception as e:
        current_app.logger.error(f"Error creating portal session: {str(e)}")
        return jsonify({'error': str(e)}), 400
