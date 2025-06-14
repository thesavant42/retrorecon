import os
import sys
from pathlib import Path

# Set environment variable before importing app
os.environ['RETRORECON_DB'] = 'envtest.db'

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


def test_env_db_loaded(monkeypatch, tmp_path):
    # point app root to temp dir
    monkeypatch.setattr(app.app, 'root_path', str(tmp_path))
    monkeypatch.setitem(app.app.config, 'DATABASE', os.path.join(str(tmp_path), 'envtest.db'))
    # create minimal schema
    (tmp_path / 'db').mkdir()
    (tmp_path / 'data').mkdir()
    schema_src = Path(__file__).resolve().parents[1] / 'db' / 'schema.sql'
    (tmp_path / 'db' / 'schema.sql').write_text(schema_src.read_text())
    app.create_new_db('envtest')

    with app.app.test_client() as client:
        client.get('/')
        with client.session_transaction() as sess:
            assert sess['db_display_name'] == 'envtest.db'

    del os.environ['RETRORECON_DB']


