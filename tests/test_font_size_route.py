import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


def setup_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    theme_dir = tmp_path / "static" / "themes"
    theme_dir.mkdir(parents=True)
    orig = Path(__file__).resolve().parents[1] / "static" / "themes" / "theme-neon.css"
    shutil.copy(orig, theme_dir / "theme-neon.css")
    monkeypatch.setattr(app, "THEMES_DIR", str(theme_dir))
    monkeypatch.setattr(app, "AVAILABLE_THEMES", ["theme-neon.css"])
    monkeypatch.setattr(app, "THEME_SWATCHES", {"theme-neon.css": ("#000", "#fff")})


def test_set_font_size_updates_css(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        resp = client.post('/set_font_size', data={'size': '16'})
        assert resp.status_code == 204
        css = (tmp_path / 'static' / 'themes' / 'theme-neon.css').read_text()
        assert css.count('font-size: 16px;') >= 8


def test_set_font_size_clamp(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        resp = client.post('/set_font_size', data={'size': '50'})
        assert resp.status_code == 204
        css = (tmp_path / 'static' / 'themes' / 'theme-neon.css').read_text()
        assert 'font-size: 18px;' in css
