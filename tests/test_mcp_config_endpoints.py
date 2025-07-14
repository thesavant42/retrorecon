"""Test MCP config API endpoints."""

import sys
import json
import tempfile
import os
from pathlib import Path

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app


def setup_tmp(monkeypatch, tmp_path):
    """Set up temporary directory for testing."""
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    (tmp_path / "data").mkdir(exist_ok=True)
    (tmp_path / "db").mkdir(exist_ok=True)
    schema = Path(__file__).resolve().parents[1] / "db" / "schema.sql"
    (tmp_path / "db" / "schema.sql").write_text(schema.read_text())
    monkeypatch.setitem(app.app.config, "DATABASE", str(tmp_path / "test.db"))
    with app.app.app_context():
        app.create_new_db("test")
    if hasattr(app, "mcp_server"):
        delattr(app, "mcp_server")


def test_get_config_empty(monkeypatch, tmp_path):
    """Test GET /api/mcp/config with no configuration file."""
    setup_tmp(monkeypatch, tmp_path)
    
    # Remove the default mcp_servers.json file if it exists
    config_file = Path("mcp_servers.json")
    if config_file.exists():
        config_file.unlink()
    
    with app.app.test_client() as client:
        resp = client.get("/api/mcp/config")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data == {'servers': []}


def test_get_config_existing(monkeypatch, tmp_path):
    """Test GET /api/mcp/config with existing configuration file."""
    setup_tmp(monkeypatch, tmp_path)
    
    with app.app.test_client() as client:
        resp = client.get("/api/mcp/config")
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'servers' in data
        assert isinstance(data['servers'], list)
        # The default config should have the fetch server
        if data['servers']:
            assert data['servers'][0]['name'] == 'fetch'


def test_update_config_valid(monkeypatch, tmp_path):
    """Test POST /api/mcp/config with valid configuration."""
    setup_tmp(monkeypatch, tmp_path)
    
    config_data = {
        'servers': [
            {
                'name': 'new-server',
                'transport': 'sse',
                'url': 'http://localhost:3000/sse',
                'enabled': True
            }
        ]
    }
    
    with app.app.test_client() as client:
        resp = client.post("/api/mcp/config", 
                          json=config_data,
                          content_type='application/json')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'message' in data
        assert 'successfully' in data['message']


def test_update_config_invalid(monkeypatch, tmp_path):
    """Test POST /api/mcp/config with invalid configuration."""
    setup_tmp(monkeypatch, tmp_path)
    
    config_data = {
        'servers': [
            {
                'name': '',  # Invalid: empty name
                'transport': 'sse',
                'url': 'http://localhost:3000/sse'
            }
        ]
    }
    
    with app.app.test_client() as client:
        resp = client.post("/api/mcp/config", 
                          json=config_data,
                          content_type='application/json')
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data
        assert 'Validation failed' in data['error']


def test_update_config_no_data(monkeypatch, tmp_path):
    """Test POST /api/mcp/config with no data."""
    setup_tmp(monkeypatch, tmp_path)
    
    with app.app.test_client() as client:
        resp = client.post("/api/mcp/config")
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data
        assert 'No data provided' in data['error']


def test_get_status(monkeypatch, tmp_path):
    """Test GET /api/mcp/status endpoint."""
    setup_tmp(monkeypatch, tmp_path)
    
    with app.app.test_client() as client:
        resp = client.get("/api/mcp/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'servers' in data
        assert isinstance(data['servers'], list)


if __name__ == '__main__':
    # Run tests directly
    print("Testing MCP config API endpoints...")
    
    # Note: These tests require the full app context, so we'll just verify the imports work
    # The actual endpoint tests would need to be run with pytest
    
    print("✓ MCP config API tests defined successfully")
    print("Run with: python -m pytest tests/test_mcp_config_endpoints.py -v")