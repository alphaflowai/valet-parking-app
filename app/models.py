from datetime import datetime
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import JSON
import pytz
import json
from time import time
import jwt
from flask import current_app
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(512))
    role = db.Column(db.String(20), nullable=False, default='customer')  # customer, manager, valet, admin
    phone_number = db.Column(db.String(20))
    venmo_username = db.Column(db.String(64))
    cashapp_username = db.Column(db.String(64))
    subscription_tier = db.Column(db.String(20))  # starter, professional, enterprise
    max_stations = db.Column(db.Integer, default=1)  # 1 for starter, unlimited for professional/enterprise
    stripe_customer_id = db.Column(db.String(120))
    subscription_id = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    google_id = db.Column(db.String(100))
    

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.first_name

    @property
    def is_professional(self):
        return self.subscription_tier == 'professional'
    
    @property
    def is_enterprise(self):
        return self.subscription_tier == 'enterprise'
    
    @property
    def dashboard_route(self):
        if self.role == 'manager':
            return 'main.manager_dashboard'
        elif self.role == 'valet':
            return 'main.valet_dashboard'
        elif self.role == 'customer':
            return 'main.customer_portal'
        return 'main.index'

    @classmethod
    def find_by_username_or_email(cls, username_or_email):
        return cls.query.filter(
            db.or_(
                cls.username == username_or_email,
                cls.email == username_or_email
            )
        ).first()

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )['reset_password']
        except:
            return None
        return User.query.get(id)

class StationManager(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subscription_status = db.Column(db.String(20), default='active')
    subscription_end = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='station_manager')
    stations = db.relationship('ValetStation', backref='manager', lazy='dynamic')

class ValetStation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    spaces = db.Column(db.String(500))  # Existing spaces field
    total_spaces = db.Column(db.Integer, default=0)  # New total_spaces field
    valet_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    valet = db.relationship('User', 
                          foreign_keys=[valet_id],
                          backref=db.backref('assigned_station', uselist=False))
    location = db.Column(db.String(200))
    manager_id = db.Column(db.Integer, db.ForeignKey('station_manager.id'))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subscription_id = db.Column(db.String(100))  # Stripe subscription ID
    
    # Relationships
    valets = db.relationship('ValetAttendant', backref='station', lazy='dynamic')
    sessions = db.relationship('Session', backref=db.backref('valet_station', lazy='joined'), lazy='dynamic')

    @property
    def completed_parkings(self):
        """Get the count of completed parkings"""
        return sum(1 for session in self.sessions if session.status == 'completed')

    @property
    def space_usage_stats(self):
        """Get space usage statistics"""
        stats = []
        if self.spaces:
            space_usage = {}
            # Calculate usage for each space
            for session in self.sessions:
                if session.parking_space:
                    space_usage[session.parking_space] = space_usage.get(session.parking_space, 0) + 1
            
            # Create stats list
            for space_number in self.spaces.split(','):
                stats.append({
                    'number': space_number,
                    'usage_count': space_usage.get(space_number, 0)
                })
        return stats

class ValetAttendant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    station_id = db.Column(db.Integer, db.ForeignKey('valet_station.id'))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    valet_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20))
    car_requested = db.Column(db.Boolean, default=False)
    qr_code_customerPortal = db.Column(db.Text)
    parking_space = db.Column(db.String(20))
    parked_time = db.Column(db.DateTime)
    retrieved_time = db.Column(db.DateTime)
    closed_parking_space = db.Column(db.String(20))
    station_id = db.Column(db.Integer, db.ForeignKey('valet_station.id'))

    valet = db.relationship('User', foreign_keys=[valet_id])
    customer = db.relationship('User', foreign_keys=[customer_id])
    car_details = db.relationship('CarDetails', backref='session', uselist=False)
    formatted_time_parked = db.Column(db.String(255))
    

    def __repr__(self):
        return f'<Session {self.ticket_number}>'

    def get_formatted_time_parked(self):
        if not self.formatted_time_parked:
            self.update_formatted_time_parked()
        try:
            return json.loads(self.formatted_time_parked)
        except json.JSONDecodeError:
            return None

    def update_formatted_time_parked(self):
        now = datetime.now(pytz.UTC)
        start_time = self.start_time.replace(tzinfo=pytz.UTC) if self.start_time.tzinfo is None else self.start_time
        time_parked = now - start_time
        hours, remainder = divmod(time_parked.total_seconds(), 3600)
        minutes, _ = divmod(remainder, 60)
        
        time_dict = {
            'hours': int(hours),
            'minutes': int(minutes)
        }
        self.formatted_time_parked = json.dumps(time_dict)
        db.session.commit()

    def to_dict(self):
        formatted_time = self.get_formatted_time_parked()
        return {
            'id': self.id,
            'ticket_number': self.ticket_number,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'valet_id': self.valet_id,
            'customer_id': self.customer_id,
            'status': self.status,
            'car_requested': self.car_requested,
            'parking_space': self.parking_space,
            'parked_time': self.parked_time.isoformat() if self.parked_time else None,
            'retrieved_time': self.retrieved_time.isoformat() if self.retrieved_time else None,
            'formatted_time_parked': formatted_time
        }

class CarDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'))
    parking_space = db.Column(db.String(20))
    color = db.Column(db.String(20))
    make = db.Column(db.String(50))
    model = db.Column(db.String(50))
    vehicle_type = db.Column(db.String(50))
    license_plate = db.Column(db.String(20))

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

def get_engine(app):
    return create_engine(
        app.config['SQLALCHEMY_DATABASE_URI'],
        poolclass=QueuePool,
        connect_args={'sslmode': 'require'} if app.config['FLASK_ENV'] == 'production' else {},
        pool_size=5,
        max_overflow=10
    )
