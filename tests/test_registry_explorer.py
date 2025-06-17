import asyncio
from pathlib import Path
import app


def setup_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    monkeypatch.setitem(app.app.config, "DATABASE", None)
    (tmp_path / "db").mkdir()
    (tmp_path / "data").mkdir()
    orig = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(app.app, "template_folder", str(orig / "templates"))
    (tmp_path / "db" / "schema.sql").write_text((orig / "db" / "schema.sql").read_text())


def test_registry_explorer_route(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    sample = [
        {
            "os": "linux",
            "architecture": "amd64",
            "layers": [{"digest": "sha256:a", "size": 1, "files": ["f"]}],
        }
    ]
    import retrorecon.routes.registry as reg

    async def fake_gather(img, method="extension"):
        assert method == "extension"
        return sample

    async def fake_digest(img):
        return "sha256:d1"

    monkeypatch.setattr(reg.rex, "gather_image_info_with_backend", fake_gather)
    monkeypatch.setattr(reg.rex, "get_manifest_digest", fake_digest)

    with app.app.test_client() as client:
        resp = client.get("/registry_explorer?image=test/test:tag&method=extension")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["manifest"] == "sha256:d1"
        assert data["platforms"][0]["layers"][0]["digest"] == "sha256:a"


def test_registry_explorer_timeout(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.registry as reg

    async def fail_gather(img, method="extension"):
        raise asyncio.TimeoutError()

    monkeypatch.setattr(reg.rex, "gather_image_info_with_backend", fail_gather)

    with app.app.test_client() as client:
        resp = client.get("/registry_explorer?image=test/test:tag")
        assert resp.status_code == 504
        assert resp.get_json()["error"] == "timeout"


def test_registry_explorer_multi_methods(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.registry as reg

    async def fake_multi(img, methods):
        assert set(methods) == {"extension", "layerslayer"}
        return {
            "extension": [
                {
                    "os": "linux",
                    "architecture": "amd64",
                    "layers": [{"digest": "sha256:a", "size": 1, "files": ["f"]}],
                }
            ],
            "layerslayer": [
                {
                    "os": "linux",
                    "architecture": "amd64",
                    "layers": [{"digest": "sha256:b", "size": 2, "files": ["g"]}],
                }
            ],
        }

    async def fake_digest(img):
        return "sha256:d2"

    monkeypatch.setattr(reg.rex, "gather_image_info_multi", fake_multi)
    monkeypatch.setattr(reg.rex, "get_manifest_digest", fake_digest)

    with app.app.test_client() as client:
        resp = client.get(
            "/registry_explorer?image=test/test:tag&methods=extension,layerslayer"
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["manifest"] == "sha256:d2"
        assert "results" in data
        assert data["results"]["extension"][0]["layers"][0]["digest"] == "sha256:a"
        assert data["results"]["layerslayer"][0]["layers"][0]["digest"] == "sha256:b"
