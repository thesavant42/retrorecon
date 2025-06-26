import io
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import retrorecon.httpolaroid_utils as utils

class FakeResp:
    def __init__(self, url, text='', content=b''):
        self.url = url
        self.text = text
        self.content = content
        self.status_code = 200
        self.headers = {}
        self.request = type('req', (), {'headers': {}})()
        class Raw:
            class Conn:
                class Sock:
                    def getpeername(self_inner):
                        return ('1.2.3.4', 0)
                sock = Sock()
            _connection = Conn()
        self.raw = Raw()
    def raise_for_status(self):
        pass


def test_capture_site_saves_js(monkeypatch):
    html = '<script src="/app.js"></script>'
    main_resp = FakeResp('http://example.com', text=html)
    js_resp = FakeResp('http://example.com/app.js', content=b'alert(1);')

    calls = []
    def fake_get(url, *a, **k):
        calls.append(url)
        if url.endswith('app.js'):
            return js_resp
        return main_resp

    monkeypatch.setattr(utils.requests, 'get', fake_get)
    monkeypatch.setattr(utils.screenshot_utils, 'take_screenshot', lambda *a, **k: (b'IMG', 200, '1.1.1.1'))

    data, screenshot, status, ip = utils.capture_site('http://example.com')
    assert status == 200
    assert ip == '1.2.3.4'
    z = io.BytesIO(data)
    with utils.zipfile.ZipFile(z) as zf:
        names = zf.namelist()
    assert any(n.startswith('assets/js') for n in names)


def test_capture_site_har_included(monkeypatch, tmp_path):
    resp = FakeResp('http://example.com', text='hello')
    monkeypatch.setattr(utils.requests, 'get', lambda *a, **k: resp)

    def fake_take(url, agent='', spoof_referrer=False, executable_path=None, log_path=None, har_path=None):
        if har_path:
            Path(har_path).write_text('{"log":{}}')
        return b'IMG', 200, '1.1.1.1'

    monkeypatch.setattr(utils.screenshot_utils, 'take_screenshot', fake_take)

    data, screenshot, status, ip = utils.capture_site('http://example.com', har_path=str(tmp_path / 't.har'))
    z = io.BytesIO(data)
    with utils.zipfile.ZipFile(z) as zf:
        assert 'harlog.json' in zf.namelist()

