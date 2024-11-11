import boto3
import json
import os

def get_database_url():
    if os.environ.get('FLASK_ENV') == 'development':
        return os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    
    # Get database URL from SSM Parameter Store
    ssm = boto3.client('ssm')
    try:
        response = ssm.get_parameter(
            Name='/valet-parking-app/database-url',
            WithDecryption=True
        )
        return response['Parameter']['Value']
    except Exception as e:
        print(f"Error fetching database URL from SSM: {e}")
        return None 