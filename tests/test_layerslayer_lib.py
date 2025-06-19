from layerslayer import parse_image_ref, registry_base_url, human_readable_size


def test_parse_image_ref():
    user, repo, tag = parse_image_ref("user/repo:tag")
    assert user == "user"
    assert repo == "repo"
    assert tag == "tag"

    user, repo, tag = parse_image_ref("ghcr.io/foo/bar:latest")
    assert user == "ghcr.io"
    assert repo == "foo/bar"
    assert tag == "latest"

    user, repo, tag = parse_image_ref("registry.k8s.io")
    assert user == "registry.k8s.io"
    assert repo == ""
    assert tag == "latest"


def test_human_readable_size():
    assert human_readable_size(2048) == "2.0 KB"


def test_registry_base_url_custom():
    assert (
        registry_base_url("ghcr.io", "homebrew/core")
        == "https://ghcr.io/v2/homebrew/core"
    )
    assert (
        registry_base_url("library", "ubuntu")
        == "https://registry-1.docker.io/v2/library/ubuntu"
    )