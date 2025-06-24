import app
from retrorecon.filters import manifest_table


def test_manifest_table_basic():
    manifest = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "config": {
            "mediaType": "application/vnd.oci.image.config.v1+json",
            "size": 10,
            "digest": "sha256:c1"
        },
        "layers": [
            {
                "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                "size": 100,
                "digest": "sha256:l1"
            }
        ]
    }
    html = manifest_table(manifest, "user/repo:tag")
    assert "sha256:l1" in html
    assert "/download_layer?image=user/repo:tag&digest=sha256:l1" in html
    assert "10.0 B" in html
    assert "100.0 B" in html
    assert "<table" in html
