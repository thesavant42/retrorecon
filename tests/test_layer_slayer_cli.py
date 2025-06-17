import runpy
import sys
from unittest import mock
import pytest
import layerslayer.fetcher as fetcher
import layerslayer.utils as utils


def run_cli(args, monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['layer_slayer.py'] + args)
    runpy.run_path('tools/layer_slayer.py', run_name='__main__')


def test_peek_layer_calls_once(monkeypatch):
    manifest = {
        'config': {'digest': 'sha256:c'},
        'layers': [
            {'digest': 'sha256:a', 'size': 1},
            {'digest': 'sha256:b', 'size': 2},
        ],
    }
    monkeypatch.setattr(fetcher, 'get_manifest', mock.Mock(return_value=manifest))
    monkeypatch.setattr(fetcher, 'fetch_build_steps', mock.Mock(return_value=[]))
    peek = mock.Mock()
    monkeypatch.setattr(fetcher, 'peek_layer_blob', peek)
    monkeypatch.setattr(utils, 'load_token', mock.Mock(return_value=None))
    run_cli(['-t', 'img:tag', '--peek-layer', '1'], monkeypatch)
    assert peek.call_count == 1
    assert peek.call_args[0][1] == 'sha256:b'


def test_peek_layer_out_of_range(monkeypatch):
    manifest = {
        'config': {'digest': 'sha256:c'},
        'layers': [{'digest': 'sha256:a', 'size': 1}],
    }
    monkeypatch.setattr(fetcher, 'get_manifest', mock.Mock(return_value=manifest))
    monkeypatch.setattr(fetcher, 'fetch_build_steps', mock.Mock(return_value=[]))
    monkeypatch.setattr(fetcher, 'peek_layer_blob', mock.Mock())
    monkeypatch.setattr(utils, 'load_token', mock.Mock(return_value=None))
    with pytest.raises(SystemExit):
        run_cli(['-t', 'img:tag', '--peek-layer', '5'], monkeypatch)


def test_log_layer_requires_file(monkeypatch):
    with pytest.raises(SystemExit):
        run_cli(['-t', 'img:tag', '--log-layer', '2'], monkeypatch)
