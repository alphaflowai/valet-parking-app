from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required
from app import db
from app.main.routes import bp
from app.models import User, Session
from app.main.forms import UserForm, CreateUserForm
from app.main.routes.auth import admin_required
from sqlalchemy import func
from datetime import datetime, timedelta
import logging

@bp.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    sessions = Session.query.all()
    return render_template('admin/dashboard.html', users=users, sessions=sessions)

@bp.route('/admin/users')
@login_required
@admin_required
def admin_users():
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=20)
    return render_template('admin/users.html', users=users)

@bp.route('/admin/sessions')
@login_required
@admin_required
def admin_sessions():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    status = request.args.get('status', '', type=str)

    query = Session.query
    if search:
        query = query.filter((Session.customer.has(username=search)) | (Session.valet.has(username=search)))
    if status:
        query = query.filter_by(status=status)

    sessions = query.paginate(page=page, per_page=15)
    return render_template('admin/sessions.html', sessions=sessions)

@bp.route('/admin/report')
@login_required
@admin_required
def admin_report():
    user_counts = db.session.query(User.role, func.count(User.id)).group_by(User.role).all()
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_sessions = Session.query.filter(Session.start_time >= thirty_days_ago).count()
    avg_duration = db.session.query(func.avg(Session.end_time - Session.start_time)).filter(Session.end_time != None).scalar()
    return render_template('admin/report.html', user_counts=dict(user_counts), recent_sessions=recent_sessions, avg_duration=avg_duration)

@bp.route('/admin/api/session_data')
@login_required
@admin_required
def admin_session_data():
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    session_counts = db.session.query(
        func.date(Session.start_time).label('date'),
        func.count(Session.id).label('count')
    ).filter(Session.start_time >= thirty_days_ago).group_by(func.date(Session.start_time)).all()
    return jsonify([{'date': str(sc.date), 'count': sc.count} for sc in session_counts])

@bp.route('/admin/create_user', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_create_user():
    form = CreateUserForm()
    if request.method == 'POST':
        if 'cancel' in request.form:
            flash('User creation cancelled.')
            return redirect(url_for('main.admin_users'))
        if form.validate_on_submit():
            try:
                user = User(first_name=form.first_name.data,
                            last_name=form.last_name.data,
                            username=form.username.data,
                            email=form.email.data,
                            phone_number=form.phone_number.data,
                            role=form.role.data,
                            venmo_username=form.venmo_username.data,
                            cashapp_username=form.cashapp_username.data)
                user.set_password(form.password.data)
                db.session.add(user)
                db.session.commit()
                flash('User created successfully.')
                return redirect(url_for('main.admin_users'))
            except Exception as e:
                db.session.rollback()
                logging.error(f"Error creating user: {str(e)}")
                flash('An error occurred while creating the user. Please try again.', 'error')
    return render_template('admin/create_user.html', title='Create User', form=form)

@bp.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(user.username, user.email)
    if form.validate_on_submit():
        try:
            user.first_name = form.first_name.data
            user.last_name = form.last_name.data
            user.username = form.username.data
            user.email = form.email.data
            user.role = form.role.data
            user.phone_number = form.phone_number.data
            user.venmo_username = form.venmo_username.data
            user.cashapp_username = form.cashapp_username.data
            if form.new_password.data:
                user.set_password(form.new_password.data)
            db.session.commit()
            flash('User updated successfully.')
            return redirect(url_for('main.admin_users'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating user: {str(e)}")
            flash('An error occurred while updating the user. Please try again.', 'error')
    elif request.method == 'GET':
        form.first_name.data = user.first_name
        form.last_name.data = user.last_name
        form.username.data = user.username
        form.email.data = user.email
        form.role.data = user.role
        form.phone_number.data = user.phone_number
    return render_template('admin/user.html', title='Edit User', form=form, user=user)
