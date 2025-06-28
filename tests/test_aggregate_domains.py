import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from retrorecon import domain_sort


def test_aggregate_and_flatten(tmp_path):
    hosts = [
        "https://web-01.prod.super.pod.example.com/foo",
        "https://web-01.prod.super.pod.example.com/bar",
        "https://mail.example.com",
    ]
    tree = domain_sort.aggregate_hosts(domain_sort.extract_hosts(hosts))
    flat = domain_sort.flatten_tree(tree)
    assert ("example.com", 3) in flat
    assert ("web-01.prod.super.pod.example.com", 2) in flat


def test_cli_flat_output(monkeypatch, capsys, tmp_path):
    data = "\n".join([
        "web-01.prod.super.pod.example.com",
        "web-02.prod.super.pod.example.com",
        "mail.example.com",
    ])
    f = tmp_path / "urls.txt"
    f.write_text(data)
    monkeypatch.setattr(sys, "argv", ["aggregate_domains.py", str(f), "--output", "flat", "--top-k", "1"])
    runpy.run_path("aggregate_domains.py", run_name="__main__")
    captured = capsys.readouterr()
    assert captured.out.strip() == "com 3"
