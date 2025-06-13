import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


def setup_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    monkeypatch.setitem(app.app.config, "DATABASE", os.path.join(str(tmp_path), "waybax.db"))
    (tmp_path / "db").mkdir()
    (tmp_path / "data").mkdir()
    orig = Path(__file__).resolve().parents[1]
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
        assert db_file.exists()
        with client.session_transaction() as sess:
            assert sess['db_display_name'] == 'waybax.db'


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
        client.post('/new_db')
        prev = app.app.config['DATABASE']
        client.post('/new_db', data={'db_name': '../bad'})
        assert app.app.config['DATABASE'] == prev
        client.post('/rename_db', data={'new_name': 'foo?bar'})
        assert app.app.config['DATABASE'] == prev


def test_rename_while_open(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        client.post('/new_db', data={'db_name': 'open'})
        conn = sqlite3.connect(app.app.config['DATABASE'])
        monkeypatch.setattr(app.os, 'rename', lambda *a, **k: (_ for _ in ()).throw(OSError('locked')))
        client.post('/rename_db', data={'new_name': 'fail'})
        assert (tmp_path / 'open.db').exists()
        conn.close()
