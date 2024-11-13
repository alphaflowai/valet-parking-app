from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, DateTimeField, TextAreaField, HiddenField, DecimalField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Optional, Regexp, NumberRange
from flask_wtf.file import FileField, FileAllowed
from valet_parking_app.app.models import User, ValetStation, Session, CarDetails
from datetime import datetime
from flask_login import current_user
from app import db
import json
import os

class UserForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[Optional()])
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('manager', 'Manager'), ('valet', 'Valet'), ('customer', 'Customer')], validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[Optional()])
    confirm_password = PasswordField('Confirm New Password', validators=[EqualTo('new_password')])
    venmo_username = StringField('Venmo Username', validators=[Optional()])
    cashapp_username = StringField('Cash App Username', validators=[Optional()])
    submit = SubmitField('Update User')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('Please use a different email address.')

class CreateUserForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[Optional()])
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone Number', validators=[Optional()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('manager', 'Manager'), ('valet', 'Valet'), ('customer', 'Customer')], validators=[DataRequired()])
    venmo_username = StringField('Venmo Username', validators=[Optional()])
    cashapp_username = StringField('Cash App Username', validators=[Optional()])
    submit = SubmitField('Create User')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class UpdateProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone Number')
    venmo_username = StringField('Venmo Username', validators=[Optional()])
    cashapp_username = StringField('Cash App Username', validators=[Optional()])
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[Optional()])
    confirm_password = PasswordField('Confirm New Password', validators=[Optional(), EqualTo('new_password')])
    submit = SubmitField('Update Profile')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(UpdateProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('Please use a different email address.')

class TicketForm(FlaskForm):
    ticket_number = StringField('Ticket Number', validators=[
        Optional(),
        Regexp(r'^[A-Za-z0-9-]*$', message="Ticket number can only contain letters, numbers, and dashes.")
    ])
    submit = SubmitField('Submit')

    def validate_ticket_number(self, field):
        if field.data:
            existing_session = Session.query.filter_by(ticket_number=field.data).first()
            if existing_session:
                raise ValidationError('This ticket number has already been used.')

class CarDetailsForm(FlaskForm):
    with open(os.path.join('app', 'static', 'data', 'vehicle_make_models.json')) as f:
        vehicle_data = json.load(f)
    vehicle_type = SelectField('Vehicle Type', choices=[
        ('car', 'Car'),
        ('suv', 'SUV'),
        ('truck', 'Truck'),
        ('van', 'Van'),
        ('motorcycle', 'Motorcycle'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    color = SelectField('Color', validators=[Optional()], choices=[(color, color) for color in vehicle_data['colors']])
    make = SelectField('Make', validators=[Optional()], choices=[(make, make) for make in vehicle_data['makes']])
    model = StringField('Model', validators=[Optional()], render_kw={"placeholder": "Enter Model"})
    license_plate = StringField('License Plate', validators=[Optional()], render_kw={"placeholder": "Enter License Plate (Optional)"})
    submit = SubmitField('Update Car Details')

    def __init__(self, *args, **kwargs):
        super(CarDetailsForm, self).__init__(*args, **kwargs)
        with open('app/static/data/vehicle_make_models.json') as f:
            vehicle_data = json.load(f)
        self.color.choices = [('', 'Select a color')] + [(color, color) for color in vehicle_data['colors']]
        self.make.choices = [('', 'Select a make')] + [(make, make) for make in vehicle_data['makes']]

    def to_dict(self):
        return {
            'vehicle_type': self.vehicle_type.data,
            'color': self.color.data,
            'make': self.make.data,
            'model': self.model.data,
            'license_plate': self.license_plate.data
        }

class ParkingSpaceForm(FlaskForm):
    parking_space = SelectField('Parking Space', validators=[DataRequired()])
    submit = SubmitField('Assign Parking Space')

    def __init__(self, *args, **kwargs):
        super(ParkingSpaceForm, self).__init__(*args, **kwargs)
        self.parking_space.choices = []  # Initialize with an empty list

class ValetAttendantForm(FlaskForm):
    id = None  # Add this line to store the user's id when editing
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[Optional()])
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone Number', validators=[Optional()])
    password = PasswordField('New Password', validators=[Optional()])
    password2 = PasswordField('Confirm New Password', validators=[Optional(), EqualTo('password')])
    confirm_password = PasswordField('Confirm New Password', validators=[Optional(), EqualTo('password')])
    assigned_station = SelectField('Assigned Station', coerce=int, validators=[Optional()])
    submit = SubmitField('Submit')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user and user.id != self.id:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user and user.id != self.id:
            raise ValidationError('Please use a different email address.')

class ValetStationForm(FlaskForm):
    name = StringField('Station Name', validators=[DataRequired()])
    valet_attendant = SelectField('Assign Valet Attendant', coerce=int)
    submit = SubmitField('Create Station')

    def validate_name(self, field):
        # Remove empty lines and whitespace
        self.name.data = ','.join(space.strip() for space in field.data.split('\n') if space.strip())

class AssignStationForm(FlaskForm):
    attendant = SelectField('Valet Attendant', coerce=int, validators=[DataRequired()])
    station = SelectField('Valet Station', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Assign')

class SpaceForm(FlaskForm):
    space = StringField('Space Name', validators=[DataRequired()])
    submit = SubmitField('Add Space')

class SMSForm(FlaskForm):
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    submit = SubmitField('Send Link')

    def validate_phone_number(self, field):
        # Remove any non-digit characters
        cleaned_number = ''.join(filter(str.isdigit, field.data))
        
        # Check if the cleaned number has a valid length
        if len(cleaned_number) < 10 or len(cleaned_number) > 15:
            raise ValidationError('Phone number must have between 10 and 15 digits.')
        
        # Check if the number starts with a valid country code
        valid_country_codes = ['1', '44', '91']  # Example: US, UK, India
        if not any(cleaned_number.startswith(code) for code in valid_country_codes):
            raise ValidationError('Invalid country code. Please use a valid international format.')
        
        # Additional checks can be added here if needed
        # For example, checking specific area codes or number patterns

class LicensePlateForm(FlaskForm):
    license_plate_image = FileField('Upload License Plate Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Upload')


class UpdateParkingSpaceForm(FlaskForm):
    parking_space = SelectField('New Parking Space', validators=[DataRequired()])
    submit = SubmitField('Update Parking Space')

    def __init__(self, available_spaces, *args, **kwargs):
        super(UpdateParkingSpaceForm, self).__init__(*args, **kwargs)
        self.parking_space.choices = [(space, space) for space in available_spaces]

class ConfirmRetrievalForm(FlaskForm):
    submit = SubmitField('Confirm Retrieval')

class LoginForm(FlaskForm):
    login = StringField('Email or Username', validators=[
        DataRequired(message='Please enter your email or username')
    ])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')
    clear = SubmitField('Clear')
    
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('customer', 'Customer'), ('valet', 'Valet'), ('manager', 'Manager'), ('admin', 'Admin')], validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

    def validate_phone_number(self, phone_number):
        user = User.query.filter_by(phone_number=phone_number.data).first()
        if user is not None:
            raise ValidationError('This phone number is already registered.')

class DonationForm(FlaskForm):
    amount = DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0.01, max=1000)])
    payment_method = SelectField('Payment Method', choices=[('venmo', 'Venmo'), ('cashapp', 'Cash App')], validators=[DataRequired()])
    submit = SubmitField('Send Donation')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')



