import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import io
import tarfile
import app


def setup_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    monkeypatch.setitem(app.app.config, "DATABASE", None)
    (tmp_path / "db").mkdir()
    (tmp_path / "data").mkdir()
    orig = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(app.app, "template_folder", str(orig / "templates"))
    (tmp_path / "db" / "schema.sql").write_text((orig / "db" / "schema.sql").read_text())


def test_dockerhub_layer_files_match(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    monkeypatch.setenv("LAYERPEEK_RANGE", "0")
    digest = "sha256:1671565cc8df8c365c9b661d3fbc164e73d01f1b0430c6179588428f99a9da2e"
    image = "migueldisney/dev:TAE-254"

    with app.app.test_client() as client:
        resp = client.get(f"/docker_layers?image={image}")
        assert resp.status_code == 200
        data = resp.get_json()
        api_files = None
        for plat in data["platforms"]:
            for layer in plat["layers"]:
                if layer["digest"] == digest:
                    api_files = layer["files"]
                    break
            if api_files is not None:
                break
        assert api_files is not None

        resp = client.get(f"/download_layer?image={image}&digest={digest}")
        assert resp.status_code == 200
        with tarfile.open(fileobj=io.BytesIO(resp.data), mode="r:gz") as tar:
            tar_files = [m.name for m in tar.getmembers()]

    assert sorted(api_files) == sorted(tar_files)

