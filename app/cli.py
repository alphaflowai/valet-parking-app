import click
from flask.cli import with_appcontext
from app import db
from app.models import User
import stripe
import os
from sqlalchemy import text

def register_commands(app):
    @app.cli.command('create-admin')
    @click.argument('username')
    @click.argument('email')
    @click.argument('phone_number')
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(username, email, phone_number, password):
        with app.app_context():
            try:
                # Use text() for raw SQL
                db.session.execute(text('COMMIT'))
                
                # Check if admin already exists
                if User.query.filter_by(username=username).first():
                    click.echo('Error: Username already exists.')
                    return
                if User.query.filter_by(email=email).first():
                    click.echo('Error: Email already exists.')
                    return

                # Create new admin user
                admin = User(
                    username=username,
                    email=email,
                    phone_number=phone_number,
                    role='admin'
                )
                admin.set_password(password)
                
                db.session.add(admin)
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

    @app.cli.command('check-duplicate-columns')
    def check_duplicate_columns():
        """Check for duplicate columns in all database tables"""
        with app.app_context():
            try:
                # Get all table names
                inspector = db.inspect(db.engine)
                tables = inspector.get_table_names()
                
                found_duplicates = False
                for table in tables:
                    columns = inspector.get_columns(table)
                    column_names = [col['name'] for col in columns]
                    
                    # Check for duplicates
                    duplicates = set([x for x in column_names if column_names.count(x) > 1])
                    
                    if duplicates:
                        found_duplicates = True
                        click.echo(f"\nDuplicate columns found in table '{table}':")
                        for dup in duplicates:
                            click.echo(f"- Column '{dup}' appears {column_names.count(dup)} times")
                
                if not found_duplicates:
                    click.echo("No duplicate columns found in any table.")
                    
            except Exception as e:
                click.echo(f"Error checking duplicate columns: {str(e)}")

    @app.cli.command('check-db-status')
    def check_db_status():
        """Check database connection and tables status"""
        with app.app_context():
            try:
                # Test database connection
                db.session.execute(text('SELECT 1'))
                click.echo('Database connection: OK')
                
                # Get all table names
                inspector = db.inspect(db.engine)
                tables = inspector.get_table_names()
                
                click.echo('\nExisting tables:')
                for table in tables:
                    # Count rows in each table
                    result = db.session.execute(text(f'SELECT COUNT(*) FROM {table}'))
                    count = result.scalar()
                    click.echo(f'- {table}: {count} rows')
                
                # Check admin users
                admin_count = User.query.filter_by(role='admin').count()
                click.echo(f'\nAdmin users: {admin_count}')
                
            except Exception as e:
                click.echo(f'Error checking database status: {str(e)}')
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