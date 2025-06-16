from pathlib import Path
import os
import sys
import types
import logging
import app


def setup_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    monkeypatch.setitem(app.app.config, "DATABASE", None)
    (tmp_path / "db").mkdir()
    (tmp_path / "data").mkdir()
    (tmp_path / "static" / "screenshots").mkdir(parents=True)
    orig = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(app.app, "template_folder", str(orig / "templates"))
    (tmp_path / "db" / "schema.sql").write_text((orig / "db" / "schema.sql").read_text())


def test_screenshotter_route(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        resp = client.get('/screenshotter')
        assert resp.status_code == 200
        assert b'id="screenshot-overlay"' in resp.data


def test_screenshot_workflow(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.app_context():
        app.create_new_db('shot')
    with app.app.test_client() as client:
        def fake_shot(url, agent, spoof):
            return b'\x89PNG\r\n\x1a\n'
        monkeypatch.setattr(app, 'take_screenshot', fake_shot)
        resp = client.post('/tools/screenshot', data={'url': 'http://example.com'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'id' in data
        resp = client.get('/screenshots')
        rows = resp.get_json()
        assert rows and rows[0]['url'] == 'http://example.com'
        sid = rows[0]['id']
        resp = client.post('/delete_screenshots', data={'ids': sid})
        assert resp.status_code == 204
        assert client.get('/screenshots').get_json() == []


def test_take_screenshot_env_path_passed(monkeypatch, tmp_path):
    setup_tmp(monkeypatch, tmp_path)

    called = {}

    class DummyPage:
        async def setUserAgent(self, ua):
            called['ua'] = ua
        async def setExtraHTTPHeaders(self, headers):
            called['hdr'] = headers
        async def goto(self, url, opts):
            called['goto'] = (url, opts)
        async def screenshot(self, fullPage=True):
            return b'PNGDATA'

    class DummyBrowser:
        async def newPage(self):
            return DummyPage()
        async def close(self):
            called['closed'] = True

    async def dummy_launch(**opts):
        called['opts'] = opts
        return DummyBrowser()

    dummy_mod = types.SimpleNamespace(launch=dummy_launch)
    monkeypatch.setitem(sys.modules, 'pyppeteer', dummy_mod)
    monkeypatch.setenv('PYPPETEER_BROWSER_PATH', '/chrome/bin')

    data = app.take_screenshot('http://example.com', user_agent='ua', spoof_referrer=True)
    assert data == b'PNGDATA'
    assert called['opts'].get('executablePath') == '/chrome/bin'


def test_take_screenshot_logs_failure(monkeypatch, tmp_path, caplog):
    setup_tmp(monkeypatch, tmp_path)

    async def fail_launch(**opts):
        raise RuntimeError('boom')

    dummy_mod = types.SimpleNamespace(launch=fail_launch)
    monkeypatch.setitem(sys.modules, 'pyppeteer', dummy_mod)
    monkeypatch.setenv('PYPPETEER_BROWSER_PATH', '/bad/path')

    caplog.set_level(logging.DEBUG)
    data = app.take_screenshot('http://example.com')
    assert data.startswith(b'\x89PNG')
    assert any('launch failed' in rec.message or 'screenshot capture failed' in rec.message for rec in caplog.records)

