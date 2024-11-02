from functools import wraps
from flask import render_template, flash, redirect, url_for, request, abort, jsonify, current_app
from flask_login import login_user, logout_user, current_user
from app import db
import stripe
from app.models import User
from app.main.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.main.routes import bp
from urllib.parse import urlparse
from app.main.routes.email import send_password_reset_email
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'manager':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def valet_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'valet':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(
            (User.email == form.login.data) | 
            (User.username == form.login.data)
        ).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username/email or password')
            return redirect(url_for('main.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('main/login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    return render_template('auth/signup.html', 
                         stripe_publishable_key=current_app.config['STRIPE_PUBLISHABLE_KEY'])

@bp.route('/api/auth/validate-account', methods=['POST'])
@csrf.exempt
def validate_account():
    data = request.get_json()
    # Validate email doesn't exist
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    return jsonify({'success': True})

def get_price_id_from_lookup(plan):
    try:
        prices = stripe.Price.list(
            lookup_keys=[f"{plan}_subscription"],
            expand=['data.product'],
            active=True
        )
        if not prices.data:
            current_app.logger.error(f"No price found for lookup key: {plan}_subscription")
            return None
        return prices.data[0].id
    except stripe.error.StripeError as e:
        current_app.logger.error(f"Stripe error looking up price: {str(e)}")
        return None

@bp.route('/api/auth/complete-signup', methods=['POST'])
def complete_signup():
    data = request.get_json()
    
    try:
        # Get price ID using lookup key
        price_id = get_price_id_from_lookup(data['plan'])
        if not price_id:
            return jsonify({'error': f"Invalid plan selected: {data['plan']}"}), 400

        # Create Stripe customer and subscription
        customer = stripe.Customer.create(
            email=data['account']['email'],
            payment_method=data['paymentMethodId'],
            invoice_settings={'default_payment_method': data['paymentMethodId']}
        )

        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{'price': price_id}],
            payment_behavior='default_incomplete',
            expand=['latest_invoice.payment_intent']
        )

        # Create user
        max_stations = None if data['plan'] == 'enterprise' else 1
        user = User(
            first_name=data['account']['first_name'],
            last_name=data['account']['last_name'],
            email=data['account']['email'],
            role='manager',
            subscription_tier=data['plan'],
            max_stations=max_stations,
            stripe_customer_id=customer.id,
            subscription_id=subscription.id
        )
        user.set_password(data['account']['password'])
        db.session.add(user)
        db.session.commit()

        login_user(user)
        return jsonify({
            'success': True,
            'redirect_url': url_for('main.manager_dashboard')
        })
    except stripe.error.StripeError as e:
        current_app.logger.error(f"Stripe error: {str(e)}")
        return jsonify({'error': str(e)}), 400

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for instructions to reset your password')
        return redirect(url_for('main.login'))
    return render_template('main/reset_password_request.html', title='Reset Password', form=form)

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('main.login'))
    return render_template('main/reset_password.html', form=form)
