import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


def setup_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    monkeypatch.setitem(app.app.config, "DATABASE", None)
    (tmp_path / "db").mkdir()
    (tmp_path / "data").mkdir()
    orig = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(app.app, "template_folder", str(orig / "templates"))
    (tmp_path / "db" / "schema.sql").write_text((orig / "db" / "schema.sql").read_text())
    demo = orig / "data" / "demo_data.json"
    if demo.exists():
        (tmp_path / "data" / "demo_data.json").write_text(demo.read_text())


def test_create_new_db_with_name(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        client.post('/new_db', data={'db_name': 'client1'})
        db_file = tmp_path / 'client1.db'
        assert db_file.exists()
        with client.session_transaction() as sess:
            assert sess['db_display_name'] == 'client1.db'
        with app.app.app_context():
            rows = app.query_db("SELECT name FROM sqlite_master WHERE type='table' AND name='urls'")
            assert rows


def test_create_new_db_default(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        client.post('/new_db')
        db_file = tmp_path / 'waybax.db'
        assert not db_file.exists()


def test_rename_database(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        client.post('/new_db', data={'db_name': 'orig'})
        with app.app.app_context():
            app.execute_db("INSERT INTO urls (url, tags) VALUES (?, ?)", ["http://a.com", ""])
        client.post('/rename_db', data={'new_name': 'renamed'})
        assert not (tmp_path / 'orig.db').exists()
        new_db = tmp_path / 'renamed.db'
        assert new_db.exists()
        with app.app.app_context():
            rows = app.query_db('SELECT url FROM urls')
            assert rows[0]['url'] == 'http://a.com'


def test_invalid_names(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        client.post('/new_db', data={'db_name': 'valid'})
        client.post('/new_db', data={'db_name': '../bad'})
        assert app.app.config['DATABASE'].endswith('bad.db')
        client.post('/rename_db', data={'new_name': 'foo?bar'})
        assert app.app.config['DATABASE'].endswith('foobar.db')


def test_rename_while_open(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        client.post('/new_db', data={'db_name': 'open'})
        conn = sqlite3.connect(app.app.config['DATABASE'])
        monkeypatch.setattr(app.os, 'rename', lambda *a, **k: (_ for _ in ()).throw(OSError('locked')))
        client.post('/rename_db', data={'new_name': 'fail'})
        assert (tmp_path / 'open.db').exists()
        conn.close()

import io
import json


def test_load_json_populates_db(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        client.post('/new_db', data={'db_name': 'import'})
        sample = [{"url": "http://wb.example/", "timestamp": "20240101010101", "status_code": 200, "mime_type": "text/html"}]
        data = json.dumps(sample).encode('utf-8')

        class DummyThread:
            def __init__(self, target, args=()):
                self.target = target
                self.args = args
            def start(self):
                self.target(*self.args)

        monkeypatch.setattr(app.threading, 'Thread', DummyThread)
        client.post('/import_file', data={'import_file': (io.BytesIO(data), 'cdx.json')})
        with app.app.app_context():
            rows = app.query_db('SELECT url, timestamp, status_code, mime_type FROM urls WHERE url = ?', ['http://wb.example/'])
            assert rows and rows[0]['timestamp'] == '20240101010101'


def test_import_db_file(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    # create a sample database that will be uploaded
    with app.app.app_context():
        sample_name = app.create_new_db('sample')
        app.execute_db("INSERT INTO urls (url, tags) VALUES (?, ?)", ['http://db.example/', ''])
    sample_bytes = (tmp_path / sample_name).read_bytes()

    with app.app.test_client() as client:
        resp = client.post('/import_file', data={'import_file': (io.BytesIO(sample_bytes), 'upload.db')})
        assert resp.status_code == 302
        with client.session_transaction() as sess:
            assert sess['db_display_name'] == 'upload.db'
        with app.app.app_context():
            rows = app.query_db('SELECT url FROM urls')
            assert rows and rows[0]['url'] == 'http://db.example/'


def test_import_invalid_db_file(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    invalid_bytes = b'not a real sqlite db'

    with app.app.test_client() as client:
        resp = client.post('/import_file', data={'import_file': (io.BytesIO(invalid_bytes), 'bad.db')})
        assert resp.status_code == 302
        with client.session_transaction() as sess:
            # Should not set db_display_name to bad.db
            assert sess.get('db_display_name') != 'bad.db'


def test_import_dsprings_db(tmp_path, monkeypatch):
    """Verify importing a populated DB preserves all rows."""
    setup_tmp(monkeypatch, tmp_path)
    db_bytes = Path(__file__).with_name('dsprings.db').read_bytes()

    with app.app.test_client() as client:
        resp = client.post('/import_file', data={'import_file': (io.BytesIO(db_bytes), 'dsprings.db')})
        assert resp.status_code == 302
        with client.session_transaction() as sess:
            assert sess['db_display_name'] == 'dsprings.db'
        with app.app.app_context():
            row = app.query_db('SELECT COUNT(*) AS c FROM urls', one=True)
            assert row['c'] == 9387


def test_save_db_custom_name(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        client.post('/new_db', data={'db_name': 'export'})
        resp = client.get('/save_db?name=mybackup')
        cd_header = resp.headers.get('Content-Disposition', '')
        assert 'attachment' in cd_header
        assert 'mybackup.db' in cd_header
        assert resp.data.startswith(b'SQLite format 3')


def test_save_db_sanitizes_period(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        client.post('/new_db', data={'db_name': 'export'})
        resp = client.get('/save_db?name=my.backup')
        cd_header = resp.headers.get('Content-Disposition', '')
        assert 'attachment' in cd_header
        assert 'my_backup.db' in cd_header


def test_session_name_reset(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        client.post('/new_db', data={'db_name': 'waybax'})
        with client.session_transaction() as sess:
            sess['db_display_name'] = 'stale.db'
        resp = client.get('/')
        assert b'loaded&gt; waybax.db' in resp.data
        with client.session_transaction() as sess:
            assert sess['db_display_name'] == 'waybax.db'


def test_new_after_rename_preserves_old_file(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        client.post('/new_db', data={'db_name': 'orig'})
        client.post('/rename_db', data={'new_name': 'renamed'})
        client.post('/new_db', data={'db_name': 'waybax'})
        assert (tmp_path / 'renamed.db').exists()
        assert (tmp_path / 'waybax.db').exists()

