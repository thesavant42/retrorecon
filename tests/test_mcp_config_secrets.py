import os
import sys
import json
from pathlib import Path


def test_mcp_config_from_secrets_file(monkeypatch, tmp_path):
    monkeypatch.delenv('RETRORECON_MCP_MODEL', raising=False)
    monkeypatch.delenv('RETRORECON_MCP_API_BASE', raising=False)
    monkeypatch.delenv('RETRORECON_MCP_TEMPERATURE', raising=False)

    secrets = tmp_path / 'secrets.json'
    secrets.write_text(json.dumps({
        'RETRORECON_MCP_MODEL': 'test-model',
        'RETRORECON_MCP_API_BASE': 'http://example.com/v1',
        'RETRORECON_MCP_TEMPERATURE': 0.55
    }))
    monkeypatch.setenv('RETRORECON_SECRETS_FILE', str(secrets))

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import importlib
    import config
    importlib.reload(config)
    from retrorecon.mcp.config import load_config

    cfg = load_config()
    assert cfg.model == 'test-model'
    assert cfg.api_base == 'http://example.com/v1'
    assert cfg.temperature == 0.55

    monkeypatch.delenv('RETRORECON_SECRETS_FILE', raising=False)
