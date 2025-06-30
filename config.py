import os
import json


def load_secrets_file(path: str = "secrets.json") -> None:
    """Load secrets from *path* into ``os.environ`` if the file exists.

    The path can be overridden by the ``RETRORECON_SECRETS_FILE`` environment
    variable. Existing environment variables are not overwritten. The secrets
    file should contain a JSON object mapping environment variable names to
    their values.
    """

    secrets_path = os.environ.get("RETRORECON_SECRETS_FILE", path)
    if not os.path.isabs(secrets_path):
        secrets_path = os.path.join(os.getcwd(), secrets_path)

    if not os.path.exists(secrets_path):
        return
    try:
        with open(secrets_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except UnicodeDecodeError:
        # Some editors on Windows may save JSON as UTF-16 with a BOM.
        # Fallback to UTF-16 if UTF-8 decoding fails.
        with open(secrets_path, "r", encoding="utf-16") as fh:
            data = json.load(fh)
    except Exception as exc:  # pragma: no cover - log only
        raise RuntimeError(f"Failed to load secrets file: {exc}") from exc

    for key, value in data.items():
        os.environ.setdefault(key, str(value))


# Load secrets before configuring the application
load_secrets_file()

class Config:
    """Application configuration loaded from environment variables or a secrets file."""

    SECRET_KEY = os.environ.get('RETRORECON_SECRET', 'CHANGE_THIS_TO_A_RANDOM_SECRET_KEY')
    DB_ENV = os.environ.get('RETRORECON_DB')
    DATABASE = None  # Will be set in app.py after app root is known
    LOG_LEVEL = os.environ.get('RETRORECON_LOG_LEVEL', 'WARNING')
    DOCKERHUB_API = os.environ.get('DOCKERHUB_API')
    VIRUSTOTAL_API = os.environ.get('VIRUSTOTAL_API')
    REGISTRY_USERNAME = os.environ.get('REGISTRY_USERNAME')
    REGISTRY_PASSWORD = os.environ.get('REGISTRY_PASSWORD')

    # Markdown editor settings
    MDEDITOR_FILE_UPLOADER = os.environ.get(
        'MDEDITOR_UPLOAD_FOLDER', os.path.join(os.getcwd(), 'uploads')
    )
    MDEDITOR_THEME = 'dark'
    MDEDITOR_PREVIEW_THEME = 'dark'
    MDEDITOR_EDITOR_THEME = 'pastel-on-dark'
