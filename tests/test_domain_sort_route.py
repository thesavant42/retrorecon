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
    # copy templates needed for dynamic rendering
    tmpl_dir = tmp_path / "templates"
    tmpl_dir.mkdir(exist_ok=True)
    orig_tmpl = Path(__file__).resolve().parents[1] / "templates" / "domain_sort.html"
    (tmpl_dir / "domain_sort.html").write_text(orig_tmpl.read_text())
    monkeypatch.setitem(app.app.config, "DATABASE", str(tmp_path / "test.db"))
    with app.app.app_context():
        app.create_new_db("test")


def test_domain_sort_markdown(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    f = tmp_path / "domains.txt"
    f.write_text("a.example.com\nb.example.com")
    with app.app.test_client() as client:
        with open(f, "rb") as fh:
            resp = client.post('/domain_sort', data={'file': fh, 'format': 'md'})
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert '### example.com' in body
        assert '- a.example.com' in body


def test_domain_sort_html(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    f = tmp_path / "domains.txt"
    f.write_text("a.example.com\nb.example.com")
    with app.app.test_client() as client:
        with open(f, 'rb') as fh:
            resp = client.post('/domain_sort', data={'file': fh})
        assert resp.status_code == 200
        text = resp.get_data(as_text=True)
        assert '<table' in text
        assert 'a.example.com' in text
        assert '<details' in text

        with app.app.app_context():
            rows = app.query_db(
                'SELECT subdomain FROM domains WHERE root_domain = ? ORDER BY subdomain',
                ['example.com']
            )
            subs = [r['subdomain'] for r in rows]
        assert subs == ['a.example.com', 'b.example.com']


def test_domain_sort_toggle_attribute(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    f = tmp_path / "domains.txt"
    f.write_text("a.example.com")
    with app.app.test_client() as client:
        with open(f, 'rb') as fh:
            resp = client.post('/domain_sort', data={'file': fh})
        text = resp.get_data(as_text=True)
    assert 'class=\'domain-sort-toggle\'' in text


def test_domain_sort_form_action():
    html = (Path(__file__).resolve().parents[1] / 'templates' / 'domain_sort.html').read_text()
    assert 'action="/domain_sort"' in html


def test_domain_sort_aggregates_all(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    f1 = tmp_path / "one.txt"
    f1.write_text("a.example.com")
    f2 = tmp_path / "two.txt"
    f2.write_text("b.other.com")
    with app.app.test_client() as client:
        with open(f1, 'rb') as fh:
            client.post('/domain_sort', data={'file': fh})
        with open(f2, 'rb') as fh:
            resp = client.post('/domain_sort', data={'file': fh})
        text = resp.get_data(as_text=True)
        assert 'a.example.com' in text
        assert 'b.other.com' in text


def test_domain_sort_get_persists(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    f = tmp_path / "domains.txt"
    f.write_text("a.example.com")
    with app.app.test_client() as client:
        with open(f, 'rb') as fh:
            client.post('/domain_sort', data={'file': fh})
        resp = client.get('/domain_sort')
        body = resp.get_data(as_text=True)
        assert 'a.example.com' in body

def test_domain_sort_includes_url_hosts(monkeypatch, tmp_path):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.app_context():
        app.execute_db(
            "INSERT INTO urls (url, domain) VALUES (?, ?)",
            ["https://foo.example.com/a", "foo.example.com"]
        )
    with app.app.test_client() as client:
        resp = client.get('/domain_sort')
        text = resp.get_data(as_text=True)
        assert 'foo.example.com' in text
