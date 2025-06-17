import os

class Config:
    """Application configuration loaded from environment variables."""

    SECRET_KEY = os.environ.get('RETRORECON_SECRET', 'CHANGE_THIS_TO_A_RANDOM_SECRET_KEY')
    DB_ENV = os.environ.get('RETRORECON_DB')
    DATABASE = None  # Will be set in app.py after app root is known
    LOG_LEVEL = os.environ.get('RETRORECON_LOG_LEVEL', 'WARNING')
