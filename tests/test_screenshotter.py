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
        assert 'preview' in rows[0]
        sid = rows[0]['id']
        resp = client.post('/delete_screenshots', data={'ids': sid})
        assert resp.status_code == 204
        assert client.get('/screenshots').get_json() == []


def test_take_screenshot_env_path_passed(monkeypatch, tmp_path):
    setup_tmp(monkeypatch, tmp_path)

    called = {}

    class DummyPage:
        def goto(self, url, wait_until=None, **kw):
            called['goto'] = (url, wait_until, kw.get('timeout'))
        def screenshot(self, full_page=True):
            return b'PNGDATA'

    class DummyContext:
        def set_extra_http_headers(self, headers):
            called['hdr'] = headers
        def new_page(self):
            return DummyPage()

    class DummyBrowser:
        def new_context(self, user_agent=None, **kw):
            called['ua'] = user_agent
            called['kw'] = kw
            return DummyContext()
        def close(self):
            called['closed'] = True

    def dummy_launch(**opts):
        called['opts'] = opts
        return DummyBrowser()

    class DummyChromium:
        def launch(self, **opts):
            return dummy_launch(**opts)

    class PW:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass
        chromium = DummyChromium()

    dummy_mod = types.SimpleNamespace(sync_playwright=lambda: PW())
    monkeypatch.setitem(sys.modules, 'playwright.sync_api', dummy_mod)
    monkeypatch.setitem(sys.modules, 'playwright', types.SimpleNamespace(sync_api=dummy_mod))
    monkeypatch.setenv('PLAYWRIGHT_CHROMIUM_PATH', '/chrome/bin')

    data = app.take_screenshot('http://example.com', user_agent='ua', spoof_referrer=True)
    assert data == b'PNGDATA'
    assert called['opts'].get('executable_path') == '/chrome/bin'


def test_take_screenshot_variable_path(monkeypatch, tmp_path):
    setup_tmp(monkeypatch, tmp_path)

    called = {}

    class DummyPage:
        def goto(self, url, wait_until=None, **kw):
            called['goto'] = (url, wait_until, kw.get('timeout'))
        def screenshot(self, full_page=True):
            return b'PNGDATA'

    class DummyContext:
        def set_extra_http_headers(self, headers):
            called['hdr'] = headers
        def new_page(self):
            return DummyPage()

    class DummyBrowser:
        def new_context(self, user_agent=None, **kw):
            called['ua'] = user_agent
            called['kw'] = kw
            return DummyContext()
        def close(self):
            called['closed'] = True

    def dummy_launch(**opts):
        called['opts'] = opts
        return DummyBrowser()

    class DummyChromium:
        def launch(self, **opts):
            return dummy_launch(**opts)

    class PW:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass
        chromium = DummyChromium()

    dummy_mod = types.SimpleNamespace(sync_playwright=lambda: PW())
    monkeypatch.setitem(sys.modules, 'playwright.sync_api', dummy_mod)
    monkeypatch.setitem(sys.modules, 'playwright', types.SimpleNamespace(sync_api=dummy_mod))
    monkeypatch.delenv('PLAYWRIGHT_CHROMIUM_PATH', raising=False)
    app.executablePath = '/alt/chrome'

    data = app.take_screenshot('http://example.com')
    assert data == b'PNGDATA'
    assert called['opts'].get('executable_path') == '/alt/chrome'
    app.executablePath = None


def test_take_screenshot_logs_failure(monkeypatch, tmp_path, caplog):
    setup_tmp(monkeypatch, tmp_path)

    def fail_launch(**opts):
        raise RuntimeError('boom')

    class DummyChromium:
        def launch(self, **opts):
            return fail_launch(**opts)

    class PW:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass
        chromium = DummyChromium()

    dummy_mod = types.SimpleNamespace(sync_playwright=lambda: PW())
    monkeypatch.setitem(sys.modules, 'playwright.sync_api', dummy_mod)
    monkeypatch.setitem(sys.modules, 'playwright', types.SimpleNamespace(sync_api=dummy_mod))
    monkeypatch.setenv('PLAYWRIGHT_CHROMIUM_PATH', '/bad/path')

    caplog.set_level(logging.DEBUG)
    data = app.take_screenshot('http://example.com')
    assert data.startswith(b'\x89PNG')
    assert any('launch failed' in rec.message or 'screenshot capture failed' in rec.message for rec in caplog.records)

