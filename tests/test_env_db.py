import os
import importlib
import sys
from pathlib import Path


def test_env_db_loaded(tmp_path):
    env_db = tmp_path / 'envtest.db'
    os.environ['RETRORECON_DB'] = str(env_db)

    sys.modules.pop('app', None)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import app as app_module
    importlib.reload(app_module)

    try:
        assert app_module.app.config['DATABASE'] == str(env_db)
        with app_module.app.test_client() as client:
            client.get('/')
            with client.session_transaction() as sess:
                assert sess['db_display_name'] == 'envtest.db'
    finally:
        del os.environ['RETRORECON_DB']

