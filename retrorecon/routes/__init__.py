from .notes import bp as notes_bp
from .tools import bp as tools_bp
from .db import bp as db_bp
from .settings import bp as settings_bp
from .urls import bp as urls_bp
from .api_client import bp as api_client_bp

__all__ = ['notes_bp', 'tools_bp', 'db_bp', 'settings_bp', 'urls_bp', 'api_client_bp']
