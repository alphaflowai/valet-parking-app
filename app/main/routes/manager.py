from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.models import User, ValetAttendant, ValetStation
from app.main.forms import ValetAttendantForm, ValetStationForm, AssignStationForm, SpaceForm
from app.main.routes.auth import manager_required

@manager_required
def manager_dashboard():
    # Get valet attendants
    valet_attendants = User.query.filter_by(role='valet').all()
    
    # Get stations
    stations = ValetStation.query.all()
    
    # Calculate max usage count for chart scaling
    max_usage_count = 0
    for station in stations:
        for space in station.space_usage_stats:
            max_usage_count = max(max_usage_count, space['usage_count'])
    
    return render_template('manager/dashboard.html',
                         valet_attendants=valet_attendants,
                         stations=stations,
                         max_usage_count=max_usage_count,
                         total_spaces=sum(len(station.spaces.split(',')) if station.spaces else 0 
                                        for station in stations))

@manager_required
def manage_valet_attendants():
    valet_attendants = User.query.filter_by(role='valet').all()
    stations = ValetStation.query.all()
    assign_form = AssignStationForm()
    assign_form.attendant.choices = [(v.id, f"{v.first_name} {v.last_name}") for v in valet_attendants]
    assign_form.station.choices = [(p.id, p.name) for p in stations]
    return render_template('manager/valet_attendants.html', valet_attendants=valet_attendants, stations=stations, assign_form=assign_form)

@manager_required
def add_valet_attendant():
    form = ValetAttendantForm()
    form.assigned_station.choices = [(0, 'Not Assigned')] + [(p.id, p.name) for p in ValetStation.query.all()]
    if form.validate_on_submit():
        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            username=form.username.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
            role='valet'
        )
        user.set_password(form.password.data)
        if form.assigned_station.data != 0:
            user.assigned_station = ValetStation.query.get(form.assigned_station.data)
        db.session.add(user)
        db.session.commit()
        flash('New valet attendant has been added.', 'success')
        return redirect(url_for('main.manage_valet_attendants'))
    return render_template('manager/valet_attendant_form.html', form=form, title="Add Valet Attendant")

@manager_required
def edit_valet_attendant(id):
    valet = User.query.filter_by(id=id, role='valet').first_or_404()
    form = ValetAttendantForm(obj=valet)
    form.password.validators = []  # Remove password validation for editing
    form.password2.validators = []
    
    # Get all stations for the dropdown
    stations = ValetStation.query.all()
    form.assigned_station.choices = [(0, 'Not Assigned')] + [(s.id, s.name) for s in stations]
    
    if form.validate_on_submit():
        valet.first_name = form.first_name.data
        valet.last_name = form.last_name.data
        valet.username = form.username.data
        valet.email = form.email.data
        valet.phone_number = form.phone_number.data
        
        if form.password.data:
            valet.set_password(form.password.data)
        
        # Handle station assignment
        if form.assigned_station.data == 0:
            # Clear any existing assignment
            if hasattr(valet, 'assigned_station') and valet.assigned_station:
                valet.assigned_station = None
        else:
            station = ValetStation.query.get(form.assigned_station.data)
            if station:
                valet.assigned_station = station
        
        try:
            db.session.commit()
            flash('Valet attendant has been updated.', 'success')
            return redirect(url_for('main.manage_valet_attendants'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating valet attendant: {str(e)}', 'error')
    
    # Pre-select the current assigned station
    if hasattr(valet, 'assigned_station') and valet.assigned_station:
        form.assigned_station.data = valet.assigned_station.id
    else:
        form.assigned_station.data = 0

    return render_template('manager/valet_attendant_form.html', form=form, title="Edit Valet Attendant")

@manager_required
def delete_valet_attendant(id):
    valet = User.query.get_or_404(id)
    db.session.delete(valet)
    db.session.commit()
    flash('Valet attendant has been deleted.')
    return redirect(url_for('main.manage_valet_attendants'))

@manager_required
def manage_stations():
    stations = ValetStation.query.all()
    
    # Check if user can add more stations based on subscription
    can_add_station = True
    if current_user.subscription_tier in ['starter', 'professional']:
        station_count = ValetStation.query.count()
        can_add_station = station_count < current_user.max_stations
    
    return render_template('manager/manage_stations.html', 
                         stations=stations, 
                         can_add_station=can_add_station,
                         subscription_tier=current_user.subscription_tier)

@manager_required
def add_station():
    station_count = ValetStation.query.count()
    
    # Check if user has reached their station limit
    if current_user.subscription_tier in ['starter', 'professional'] and station_count >= current_user.max_stations:
        flash('Your current subscription plan only allows for one valet station. Please upgrade your plan to add more stations.', 'error')
        return redirect(url_for('main.manage_stations'))
    
    form = ValetStationForm()
    valets = User.query.filter_by(role='valet').all()
    form.valet_attendant.choices = [(0, 'Not Assigned')] + [(v.id, f"{v.first_name} {v.last_name}") for v in valets]
    
    if form.validate_on_submit():
        try:
            station = ValetStation(name=form.name.data)
            if form.valet_attendant.data != 0:
                valet = User.query.get(form.valet_attendant.data)
                valet.assigned_station = station
            db.session.add(station)
            db.session.commit()
            flash('Station created successfully!', 'success')
            return redirect(url_for('main.manage_spaces', station_id=station.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating station: {str(e)}', 'error')
    return render_template('manager/station_form.html', form=form, title="Add New Station")

@manager_required
def edit_station(id):
    station = ValetStation.query.get_or_404(id)
    form = ValetStationForm(obj=station)
    if form.validate_on_submit():
        station.name = form.name.data
        station.spaces = form.spaces.data
        db.session.commit()
        flash('Station has been updated.')
        return redirect(url_for('main.manage_stations'))
    return render_template('manager/station_form.html', form=form, title="Edit Station")

@manager_required
def delete_station(id):
    station = ValetStation.query.get_or_404(id)
    db.session.delete(station)
    db.session.commit()
    flash('Station has been deleted.')
    return redirect(url_for('main.manage_stations'))

@manager_required
def assign_valet_to_station():
    form = AssignStationForm()
    valet_attendants = User.query.filter_by(role='valet').all()
    form.attendant.choices = [(v.id, f"{v.first_name} {v.last_name}") for v in valet_attendants]
    form.station.choices = [(p.id, p.name) for p in ValetStation.query.all()]

    if form.validate_on_submit():
        valet = User.query.get(form.attendant.data)
        station = ValetStation.query.get(form.station.data)
        
        # Clear any existing assignment for this valet
        if valet.assigned_station:
            valet.assigned_station = None
            
        # Update the station's valet reference
        station.valet = valet
        db.session.commit()
        
        flash(f'Valet {valet.first_name} {valet.last_name} has been assigned to station {station.name}.')
        return redirect(url_for('main.manage_valet_attendants'))

    flash('Invalid form submission.', 'error')
    return redirect(url_for('main.manage_valet_attendants'))

@manager_required
def manage_spaces(station_id):
    station = ValetStation.query.get_or_404(station_id)
    form = SpaceForm()
    return render_template('manager/manage_spaces.html', station=station, form=form)

@manager_required
def add_space(station_id):
    station = ValetStation.query.get_or_404(station_id)
    form = SpaceForm()
    
    if form.validate_on_submit():
        new_space = form.space.data
        current_spaces = station.spaces.split(',') if station.spaces else []
        if new_space not in current_spaces:
            current_spaces.append(new_space)
            station.spaces = ','.join(filter(None, current_spaces))  # filter out empty strings
            db.session.commit()
            flash(f'Space {new_space} added to station {station.name}.', 'success')
        else:
            flash(f'Space {new_space} already exists in station {station.name}.', 'error')
    return redirect(url_for('main.manage_spaces', station_id=station.id))

@manager_required
def edit_space(station_id, old_space):
    station = ValetStation.query.get_or_404(station_id)
    new_space = request.form.get('new_space')
    if new_space and new_space != old_space:
        current_spaces = station.spaces.split(',') if station.spaces else []
        if old_space in current_spaces:
            index = current_spaces.index(old_space)
            current_spaces[index] = new_space
            station.spaces = ','.join(current_spaces)
            db.session.commit()
            flash(f'Space {old_space} renamed to {new_space} in station {station.name}.', 'success')
        else:
            flash(f'Space {old_space} not found in station {station.name}.', 'error')
    return redirect(url_for('main.manage_spaces', station_id=station.id))

@manager_required
def delete_space(station_id, space):
    station = ValetStation.query.get_or_404(station_id)
    current_spaces = station.spaces.split(',') if station.spaces else []
    if space in current_spaces:
        current_spaces.remove(space)
        station.spaces = ','.join(current_spaces)
        db.session.commit()
        flash(f'Space {space} removed from station {station.name}.', 'success')
    else:
        flash(f'Space {space} not found in station {station.name}.', 'error')
    return redirect(url_for('main.manage_spaces', station_id=station.id))