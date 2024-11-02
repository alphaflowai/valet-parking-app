import click
from flask.cli import with_appcontext
from app.__init__ import db
from app.models import User
import stripe
import time
import os

@click.command('create-admin')
@click.argument('username')
@click.argument('email')
@click.argument('phone_number')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
@with_appcontext
def create_admin(username, email, phone_number, password):
    user = User.query.filter_by(username=username).first()
    if user is not None:
        click.echo('Error: Username already exists.')
        return

    user = User.query.filter_by(email=email).first()
    if user is not None:
        click.echo('Error: Email already exists.')
        return

    user = User(username=username, email=email, phone_number=phone_number, role='admin')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo(f'Admin user {username} created successfully.')

@click.command('create-manager')
@click.argument('username')
@click.argument('email')
@click.password_option()
@with_appcontext
def create_manager(username, email, password):
    user = User(username=username, email=email, role='manager')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo(f'Manager user {username} created.')

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

def init_app(app):
    app.cli.add_command(create_admin)
    app.cli.add_command(create_manager)
    app.cli.add_command(setup_stripe_command)