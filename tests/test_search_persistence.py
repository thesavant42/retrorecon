import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


def setup_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    (tmp_path / "data").mkdir(exist_ok=True)
    (tmp_path / "db").mkdir(exist_ok=True)
    schema = Path(__file__).resolve().parents[1] / "db" / "schema.sql"
    (tmp_path / "db" / "schema.sql").write_text(schema.read_text())
    monkeypatch.setitem(app.app.config, "DATABASE", str(tmp_path / "test.db"))
    with app.app.app_context():
        app.create_new_db("test")
    import retrorecon.routes.dynamic as dyn
    monkeypatch.setattr(dyn, "dynamic_template", lambda *a, **k: "")


def test_query_persists_after_delete(monkeypatch, tmp_path):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        resp = client.get('/?q=.json')
        assert resp.status_code == 200
        with client.session_transaction() as sess:
            assert sess.get('search_query') == '.json'
        resp = client.post('/bulk_action', data={'action': 'delete', 'selected_ids': ['1']})
        assert resp.status_code == 302
        resp = client.get('/')
        assert resp.status_code == 200
        with client.session_transaction() as sess:
            assert sess.get('search_query') == '.json'
