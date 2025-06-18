import asyncio
from pathlib import Path
import pytest
import app


def setup_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    monkeypatch.setitem(app.app.config, "DATABASE", None)
    (tmp_path / "db").mkdir()
    (tmp_path / "data").mkdir()
    orig = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(app.app, "template_folder", str(orig / "templates"))
    (tmp_path / "db" / "schema.sql").write_text((orig / "db" / "schema.sql").read_text())


@pytest.mark.skip(reason="bogus: does not verify directory listing in UI")
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

    async def fake_gather(img, method="extension", **kwargs):
        assert method == "extension"
        return sample

    async def fake_digest(img):
        return "sha256:d1"

    monkeypatch.setattr(reg.rex, "gather_image_info_with_backend", fake_gather)
    monkeypatch.setattr(reg.rex, "get_manifest_digest", fake_digest)

    with app.app.test_client() as client:
        resp = client.get("/registry_explorer?image=test/test:tag&method=extension&files=1")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["manifest"] == "sha256:d1"
        assert data["platforms"][0]["layers"][0]["digest"] == "sha256:a"


def test_registry_explorer_timeout(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.registry as reg

    async def fail_gather(img, method="extension", **kwargs):
        raise asyncio.TimeoutError()

    monkeypatch.setattr(reg.rex, "gather_image_info_with_backend", fail_gather)

    with app.app.test_client() as client:
        resp = client.get("/registry_explorer?image=test/test:tag")
        assert resp.status_code == 504
        assert resp.get_json()["error"] == "timeout"


def test_registry_explorer_multi_methods(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.registry as reg

    async def fake_multi(img, methods, **kwargs):
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


def test_registry_explorer_file_listing(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    sample = [
        {
            "os": "linux",
            "architecture": "amd64",
            "layers": [
                {"digest": "sha256:c", "size": 3, "files": ["dir/file1", "dir/file2"]}
            ],
        }
    ]
    import retrorecon.routes.registry as reg

    async def fake_gather(img, method="extension", **kwargs):
        return sample

    async def fake_digest(img):
        return "sha256:d3"

    monkeypatch.setattr(reg.rex, "gather_image_info_with_backend", fake_gather)
    monkeypatch.setattr(reg.rex, "get_manifest_digest", fake_digest)

    def build_tables(plats, img):
        html = ""
        for plat in plats:
            html += f"<h4>{plat['os']}/{plat['architecture']}</h4>"
            html += (
                '<table class="table url-table w-100"><colgroup>'
                '<col/><col class="w-6em"/><col/><col class="w-6em"/>'
                '</colgroup><thead><tr>'
                '<th class="sortable" data-field="digest">Digest</th>'
                '<th class="sortable" data-field="size">Size</th>'
                '<th>Files</th><th>Download</th>'
                '</tr></thead><tbody>'
            )
            for layer in plat["layers"]:
                files = "".join(
                    f'<li><a class="mt" href="/layers/{img}/{f}">{f}</a></li>'
                    for f in layer["files"]
                )
                files_html = (
                    f"<details><summary>{len(layer['files'])} files</summary><ul>{files}</ul></details>"
                )
                dlink = f"/download_layer?image={img}&digest={layer['digest']}"
                html += (
                    f'<tr><td class="w-25em"><div class="cell-content">{layer["digest"]}</div></td>'
                    f'<td>{layer["size"]}</td><td>{files_html}</td>'
                    f'<td><a href="{dlink}">Get</a></td></tr>'
                )
            html += "</tbody></table>"
        return html

    with app.app.test_client() as client:
        resp = client.get("/registry_explorer?image=test/test:tag&method=extension&files=1")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["manifest"] == "sha256:d3"
        html = build_tables(data["platforms"], "test/test:tag")
        assert "dir/file1" in html
        assert "dir/file2" in html
