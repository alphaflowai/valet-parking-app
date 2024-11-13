import click
from flask.cli import with_appcontext
from app import db
from app.models import User
import stripe
import os

def register_commands(app):
    @app.cli.command('create-admin')
    @click.argument('username')
    @click.argument('email')
    @click.argument('phone_number')
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(username, email, phone_number, password):
        with app.app_context():
            try:
                db.session.execute('COMMIT')  # Ensure no transaction is pending
                
                # Validate existing user
                if User.query.filter_by(username=username).first():
                    click.echo('Error: Username already exists.')
                    return
                if User.query.filter_by(email=email).first():
                    click.echo('Error: Email already exists.')
                    return

                # Create new user
                user = User(
                    username=username,
                    email=email,
                    phone_number=str(phone_number),
                    role='admin'
                )
                user.set_password(password)
                
                db.session.add(user)
                db.session.commit()
                
                click.echo(f'Admin user {username} created successfully!')
                
            except Exception as e:
                db.session.rollback()
                click.echo(f'Error creating admin user: {str(e)}')

    @app.cli.command('create-manager')
    @click.argument('username')
    @click.argument('email')
    @click.argument('phone_number')
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
    def create_manager(username, email, phone_number, password):
        with app.app_context():
            user = User.query.filter_by(username=username).first()
            if user is not None:
                click.echo('Error: Username already exists.')
                return

            user = User.query.filter_by(email=email).first()
            if user is not None:
                click.echo('Error: Email already exists.')
                return

            user = User(username=username, email=email, phone_number=phone_number, role='manager')
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            click.echo(f'Manager user {username} created successfully.')

    @app.cli.command('check-admin')
    def check_admin():
        """Check if admin exists, create one if not"""
        with app.app_context():
            try:
                # Check for any admin user
                admin = User.query.filter_by(role='admin').first()
                
                if admin:
                    click.echo('Admin user exists:')
                    click.echo(f'Username: {admin.username}')
                    click.echo(f'Email: {admin.email}')
                else:
                    click.echo('No admin user found. Creating default admin...')
                    
                    # Create default admin
                    admin = User(
                        username='admin',
                        email='sendtocomplete@gmail.com',
                        phone_number='+1234567890',
                        role='admin'
                    )
                    admin.set_password('admin123')  # Set a default password
                    
                    db.session.add(admin)
                    db.session.commit()
                    
                    click.echo('Default admin created:')
                    click.echo('Username: admin')
                    click.echo('Email: sendtocomplete@gmail.com')
                    click.echo('Password: admin123')
                    click.echo('Please change the password after first login!')
                    
            except Exception as e:
                db.session.rollback()
                click.echo(f'Error checking/creating admin: {str(e)}')
                raise

@click.command('setup-stripe')
@with_appcontext
def setup_stripe_command():
    """Initialize Stripe products and prices"""
    try:
        # Create new product with unique name
        timestamp = int(time.time())
        product = stripe.Product.create(
            name=f"Valet Parking Service {timestamp}",
            description="Professional valet parking management system"
        )

        # Define prices with unique lookup keys
        prices = [
            {
                "amount": 6000,
                "interval": "week",
                "lookup_key": f"starter_subscription_{timestamp}",
                "nickname": "Starter Plan"
            },
            {
                "amount": 12500,
                "interval": "week",
                "lookup_key": f"professional_subscription_{timestamp}",
                "nickname": "Professional Plan"
            },
            {
                "amount": 500000,
                "interval": "month",
                "lookup_key": f"enterprise_subscription_{timestamp}",
                "nickname": "Enterprise Plan"
            }
        ]

        created_prices = []
        for price in prices:
            new_price = stripe.Price.create(
                product=product.id,
                unit_amount=price["amount"],
                currency="usd",
                recurring={"interval": price["interval"]},
                lookup_key=price["lookup_key"],
                nickname=price["nickname"]
            )
            created_prices.append(new_price)

        # Store the new price IDs in environment variables
        os.environ['STRIPE_STARTER_PRICE_ID'] = created_prices[0].id
        os.environ['STRIPE_PROFESSIONAL_PRICE_ID'] = created_prices[1].id
        os.environ['STRIPE_ENTERPRISE_PRICE_ID'] = created_prices[2].id

        click.echo("Successfully set up Stripe products and prices!")
        click.echo(f"Starter Price ID: {created_prices[0].id}")
        click.echo(f"Professional Price ID: {created_prices[1].id}")
        click.echo(f"Enterprise Price ID: {created_prices[2].id}")
        
    except stripe.error.StripeError as e:
        click.echo(f"Error setting up Stripe: {str(e)}", err=True)