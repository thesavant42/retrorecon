import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


def test_domain_sort_markdown(tmp_path):
    f = tmp_path / "domains.txt"
    f.write_text("a.example.com\nb.example.com")
    with app.app.test_client() as client:
        with open(f, "rb") as fh:
            resp = client.post('/domain_sort', data={'file': fh, 'format': 'md'})
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert '### example.com' in body
        assert '- a.example.com' in body


def test_domain_sort_html(tmp_path):
    f = tmp_path / "domains.txt"
    f.write_text("a.example.com\nb.example.com")
    with app.app.test_client() as client:
        with open(f, 'rb') as fh:
            resp = client.post('/domain_sort', data={'file': fh})
        assert resp.status_code == 200
        text = resp.get_data(as_text=True)
        assert '<table' in text
        assert 'a.example.com' in text
