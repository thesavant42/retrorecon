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


def test_docker_layers_route(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    sample = [
        {
            "os": "linux",
            "architecture": "amd64",
            "layers": [
                {"digest": "sha256:a", "size": 1, "files": ["f"]}
            ],
        }
    ]
    import retrorecon.routes.docker as docker_mod

    async def fake_gather(img):
        return sample

    monkeypatch.setattr(docker_mod, "gather_layers_info", fake_gather)
    with app.app.test_client() as client:
        resp = client.get('/docker_layers?image=test/test:latest')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data[0]["layers"][0]["digest"] == "sha256:a"
