from flask import render_template
from flask_login import login_required, current_user
from valet_parking_app.app.models import ValetStation
from app.main.routes.auth import manager_required

@bp.route('/manager/dashboard')
@login_required
@manager_required
def manager_dashboard():
    user = current_user
    stations = ValetStation.query.filter_by(manager_id=user.id).all()
    
    # For starter plan, enforce single station limit
    if user.subscription_tier == 'starter' and len(stations) >= 1:
        can_create_station = False
    else:
        can_create_station = True
    
    return render_template('dashboard/manager_dashboard.html',
                         stations=stations,
                         can_create_station=can_create_station,
                         is_professional=user.is_professional) 