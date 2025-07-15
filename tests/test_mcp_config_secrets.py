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
        'RETRORECON_MCP_TEMPERATURE': 0.55,
        'RETRORECON_MCP_TIMEOUT': 42,
        'RETRORECON_MCP_ALT_API_BASES': 'http://alt1.example.com/v1,http://alt2.example.com/v1'
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
    assert cfg.timeout == 42
    assert cfg.fallback_api_bases == ['http://alt1.example.com/v1', 'http://alt2.example.com/v1']

    monkeypatch.delenv('RETRORECON_SECRETS_FILE', raising=False)


def test_alt_api_base_missing_protocol(monkeypatch):
    monkeypatch.setenv('RETRORECON_MCP_ALT_API_BASES', 'alt1.example.com/v1')
    from retrorecon.mcp.config import load_config

    cfg = load_config()
    assert cfg.fallback_api_bases == ['http://alt1.example.com/v1']
    monkeypatch.delenv('RETRORECON_MCP_ALT_API_BASES', raising=False)


def test_fallback_api_base_missing_protocol(monkeypatch):
    monkeypatch.setenv('RETRORECON_MCP_FALLBACK_API_BASES', 'fallback1.example.com/v1')
    from retrorecon.mcp.config import load_config

    cfg = load_config()
    assert cfg.fallback_api_bases == ['http://fallback1.example.com/v1']
    monkeypatch.delenv('RETRORECON_MCP_FALLBACK_API_BASES', raising=False)


def test_flask_port_warning(monkeypatch):
    monkeypatch.setenv('RETRORECON_MCP_API_BASE', 'http://127.0.0.1:5000/v1')
    from retrorecon.mcp.config import load_config

    cfg = load_config()
    assert cfg.api_base == 'http://127.0.0.1:5000/v1'  # Should still work but with warning
    monkeypatch.delenv('RETRORECON_MCP_API_BASE', raising=False)
