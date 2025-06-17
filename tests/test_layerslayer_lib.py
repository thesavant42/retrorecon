from layerslayer import parse_image_ref, human_readable_size


def test_parse_image_ref():
    user, repo, tag = parse_image_ref("user/repo:tag")
    assert user == "user"
    assert repo == "repo"
    assert tag == "tag"


def test_human_readable_size():
    assert human_readable_size(2048) == "2.0 KB"
