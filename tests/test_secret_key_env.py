import os
import sys
from pathlib import Path

os.environ['RETRORECON_SECRET'] = 'sup3rsecret'

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import importlib
import config
importlib.reload(config)
import app
importlib.reload(app)


def test_secret_key_loaded(monkeypatch, tmp_path):
    monkeypatch.setattr(app.app, 'root_path', str(tmp_path))
    with app.app.app_context():
        assert app.app.secret_key == 'sup3rsecret'
    del os.environ['RETRORECON_SECRET']
