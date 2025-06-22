import os
import sys
import json
from pathlib import Path


def test_secret_key_from_secrets_file(monkeypatch, tmp_path):
    monkeypatch.delenv('RETRORECON_SECRET', raising=False)
    secrets = tmp_path / 'secrets.json'
    secrets.write_text(json.dumps({'RETRORECON_SECRET': 'filekey'}))
    monkeypatch.setenv('RETRORECON_SECRETS_FILE', str(secrets))

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import importlib
    import config
    importlib.reload(config)
    import app
    importlib.reload(app)

    monkeypatch.setattr(app.app, 'root_path', str(tmp_path))
    with app.app.app_context():
        assert app.app.secret_key == 'filekey'

    monkeypatch.delenv('RETRORECON_SECRETS_FILE', raising=False)
    monkeypatch.delenv('RETRORECON_SECRET', raising=False)


def test_secret_key_utf16_file(monkeypatch, tmp_path):
    monkeypatch.delenv('RETRORECON_SECRET', raising=False)
    secrets = tmp_path / 'secrets.json'
    secrets.write_text(json.dumps({'RETRORECON_SECRET': 'utf16key'}), encoding='utf-16')
    monkeypatch.setenv('RETRORECON_SECRETS_FILE', str(secrets))

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import importlib
    import config
    importlib.reload(config)
    import app
    importlib.reload(app)

    monkeypatch.setattr(app.app, 'root_path', str(tmp_path))
    with app.app.app_context():
        assert app.app.secret_key == 'utf16key'

    monkeypatch.delenv('RETRORECON_SECRETS_FILE', raising=False)
    monkeypatch.delenv('RETRORECON_SECRET', raising=False)

