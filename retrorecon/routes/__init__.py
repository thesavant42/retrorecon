from .notes import bp as notes_bp
from .tools import bp as tools_bp
from .db import bp as db_bp
from .settings import bp as settings_bp
from .domains import bp as domains_bp
from .docker import bp as docker_bp
from .registry import bp as registry_bp
from .dag import bp as dag_bp
from .oci import bp as oci_bp
from .dagdotdev import bp as dagdotdev_bp
from .urls import bp as urls_bp
from .swagger import bp as swagger_bp
from .overview import bp as overview_bp
from .tags import bp as tags_bp
from .assets import bp as assets_bp
from .import_routes import bp as import_bp
from .status import bp as status_bp

__all__ = [
    'notes_bp', 'tools_bp', 'db_bp', 'settings_bp', 'domains_bp',
    'docker_bp', 'registry_bp', 'dag_bp', 'oci_bp', 'dagdotdev_bp',
    'urls_bp', 'swagger_bp', 'overview_bp', 'tags_bp',
    'assets_bp', 'import_bp', 'status_bp'
]
