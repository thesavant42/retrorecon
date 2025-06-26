import io
from pathlib import Path
import sys
import pytest
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

@pytest.mark.xfail(reason="https://github.com/thesavant42/retrorecon/issues/705")
def test_capture_site_saves_css(monkeypatch):
    html = '<link rel="stylesheet" href="/style.css">'
    main_resp = FakeResp('http://example.com', text=html)
    css_resp = FakeResp('http://example.com/style.css', content=b'body{}')

    def fake_get(url, *a, **k):
        if url.endswith('style.css'):
            return css_resp
        return main_resp

    monkeypatch.setattr(utils.requests, 'get', fake_get)
    monkeypatch.setattr(utils.screenshot_utils, 'take_screenshot', lambda *a, **k: (b'IMG', 200, '1.1.1.1'))

    data, screenshot, status, ip = utils.capture_site('http://example.com')
    z = io.BytesIO(data)
    with utils.zipfile.ZipFile(z) as zf:
        names = zf.namelist()
    assert any('style.css' in n for n in names)

@pytest.mark.xfail(reason="https://github.com/thesavant42/retrorecon/issues/705")
def test_capture_site_saves_images(monkeypatch):
    html = '<img src="/img/logo.png">'
    main_resp = FakeResp('http://example.com', text=html)
    img_resp = FakeResp('http://example.com/img/logo.png', content=b'IMGDATA')

    def fake_get(url, *a, **k):
        if url.endswith('logo.png'):
            return img_resp
        return main_resp

    monkeypatch.setattr(utils.requests, 'get', fake_get)
    monkeypatch.setattr(utils.screenshot_utils, 'take_screenshot', lambda *a, **k: (b'IMG', 200, '1.1.1.1'))

    data, screenshot, status, ip = utils.capture_site('http://example.com')
    z = io.BytesIO(data)
    with utils.zipfile.ZipFile(z) as zf:
        names = zf.namelist()
    assert any('logo.png' in n for n in names)

@pytest.mark.xfail(reason="https://github.com/thesavant42/retrorecon/issues/705")
def test_capture_site_saves_fonts(monkeypatch):
    html = '<link rel="stylesheet" href="/style.css">'
    main_resp = FakeResp('http://example.com', text=html)
    css_resp = FakeResp('http://example.com/style.css', content=b"@font-face{src:url('/fonts/foo.woff2');}")
    font_resp = FakeResp('http://example.com/fonts/foo.woff2', content=b'FONTDATA')

    def fake_get(url, *a, **k):
        if url.endswith('style.css'):
            return css_resp
        if url.endswith('foo.woff2'):
            return font_resp
        return main_resp

    monkeypatch.setattr(utils.requests, 'get', fake_get)
    monkeypatch.setattr(utils.screenshot_utils, 'take_screenshot', lambda *a, **k: (b'IMG', 200, '1.1.1.1'))

    data, screenshot, status, ip = utils.capture_site('http://example.com')
    z = io.BytesIO(data)
    with utils.zipfile.ZipFile(z) as zf:
        names = zf.namelist()
    assert any('foo.woff2' in n for n in names)
