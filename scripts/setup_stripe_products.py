import os
import stripe
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def create_product_and_prices():
    try:
        # Create the main product
        product = stripe.Product.create(
            name="Valet Parking Service",
            description="Professional valet parking management system"
        )

        # Create prices with lookup keys
        prices = [
            {
                "amount": 6000,
                "interval": "week",
                "lookup_key": "starter_subscription"
            },
            {
                "amount": 12500,
                "interval": "week",
                "lookup_key": "professional_subscription"
            },
            {
                "amount": 500000,
                "interval": "month",
                "lookup_key": "enterprise_subscription"
            }
        ]

        for price in prices:
            stripe.Price.create(
                product=product.id,
                unit_amount=price["amount"],
                currency="usd",
                recurring={"interval": price["interval"]},
                lookup_key=price["lookup_key"]
            )

        print("Successfully created product and prices!")
        
    except stripe.error.StripeError as e:
        print(f"Error creating Stripe products: {str(e)}")

if __name__ == "__main__":
    create_product_and_prices() 