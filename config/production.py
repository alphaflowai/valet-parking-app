from config.base import Config

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    WTF_CSRF_ENABLED = True
    # Add other production-specific settings