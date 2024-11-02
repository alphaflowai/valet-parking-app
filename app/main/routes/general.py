from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.models import User
from app.main.forms import UpdateProfileForm
from werkzeug.security import check_password_hash
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('main.admin_dashboard'))
        elif current_user.role == 'manager':
            return redirect(url_for('main.manager_dashboard'))
        elif current_user.role == 'valet':
            return redirect(url_for('main.valet_dashboard'))
    return render_template('index.html')

@login_required
def user_profile():
    form = UpdateProfileForm(current_user.username, current_user.email)
    if form.validate_on_submit():
        if check_password_hash(current_user.password_hash, form.current_password.data):
            current_user.username = form.username.data
            current_user.email = form.email.data
            current_user.phone_number = form.phone_number.data
            if form.new_password.data:
                current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Your profile has been updated.')
            return redirect(url_for('main.user_profile'))
        else:
            flash('Incorrect current password.')
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.phone_number.data = current_user.phone_number
    return render_template('user_profile.html', title='User Profile', form=form)