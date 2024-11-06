from config.base import Config

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    # Add any development-specific settings here