"""
Tests for MCP web management interface.
"""
import json
import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app
from retrorecon.routes.mcp_management import bp as mcp_management_bp


@pytest.fixture
def client():
    """Create a test client."""
    app.app.config['TESTING'] = True
    with app.app.test_client() as client:
        yield client


@pytest.fixture
def mock_manager():
    """Create a mock MCP manager."""
    manager = Mock()
    
    # Create a proper mock status object
    mock_status = Mock()
    mock_status.name = "test_module"
    mock_status.enabled = True
    mock_status.running = True
    mock_status.transport = "stdio"
    mock_status.tools = ["tool1", "tool2"]
    mock_status.last_started = 1234567890.0
    mock_status.last_error = None
    mock_status.health_check_url = None
    
    manager.get_all_module_status.return_value = {
        "test_module": mock_status
    }
    manager.check_module_health.return_value = True
    manager.check_all_health.return_value = {"test_module": True}
    manager.restart_unhealthy_modules.return_value = []
    return manager


def test_mcp_status_route(client, mock_manager):
    """Test MCP status route."""
    with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=mock_manager):
        response = client.get('/mcp/status')
        
        assert response.status_code == 200
        data = response.get_json()
        assert "test_module" in data
        assert data["test_module"]["running"] is True
        assert data["test_module"]["transport"] == "stdio"
        assert data["test_module"]["tools"] == ["tool1", "tool2"]


def test_mcp_status_route_no_manager(client):
    """Test MCP status route when manager is not available."""
    with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=None):
        response = client.get('/mcp/status')
        
        assert response.status_code == 500
        data = response.get_json()
        assert "MCP manager not initialized" in data["error"]


def test_start_module_route(client, mock_manager):
    """Test start module route."""
    with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=mock_manager):
        response = client.post('/mcp/start/test_module')
        
        assert response.status_code == 200
        data = response.get_json()
        assert "Started module: test_module" in data["message"]
        mock_manager.start.assert_called_once_with('test_module')


def test_start_module_route_error(client, mock_manager):
    """Test start module route with error."""
    mock_manager.start.side_effect = Exception("Start failed")
    
    with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=mock_manager):
        response = client.post('/mcp/start/test_module')
        
        assert response.status_code == 500
        data = response.get_json()
        assert "Start failed" in data["error"]


def test_stop_module_route(client, mock_manager):
    """Test stop module route."""
    with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=mock_manager):
        response = client.post('/mcp/stop/test_module')
        
        assert response.status_code == 200
        data = response.get_json()
        assert "Stopped module: test_module" in data["message"]
        mock_manager.stop.assert_called_once_with('test_module')


def test_restart_module_route(client, mock_manager):
    """Test restart module route."""
    with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=mock_manager):
        response = client.post('/mcp/restart/test_module')
        
        assert response.status_code == 200
        data = response.get_json()
        assert "Restarted module: test_module" in data["message"]
        mock_manager.restart.assert_called_once_with('test_module')


def test_health_single_module_route(client, mock_manager):
    """Test health check for single module route."""
    with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=mock_manager):
        response = client.get('/mcp/health/test_module')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["module"] == "test_module"
        assert data["healthy"] is True
        mock_manager.check_module_health.assert_called_once_with('test_module')


def test_health_all_modules_route(client, mock_manager):
    """Test health check for all modules route."""
    with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=mock_manager):
        response = client.get('/mcp/health')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["test_module"] is True
        mock_manager.check_all_health.assert_called_once()


def test_start_all_modules_route(client, mock_manager):
    """Test start all modules route."""
    with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=mock_manager):
        response = client.post('/mcp/start-all')
        
        assert response.status_code == 200
        data = response.get_json()
        assert "Started all enabled modules" in data["message"]
        mock_manager.start_all.assert_called_once()


def test_stop_all_modules_route(client, mock_manager):
    """Test stop all modules route."""
    with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=mock_manager):
        response = client.post('/mcp/stop-all')
        
        assert response.status_code == 200
        data = response.get_json()
        assert "Stopped all modules" in data["message"]
        mock_manager.stop_all.assert_called_once()


def test_restart_unhealthy_modules_route(client, mock_manager):
    """Test restart unhealthy modules route."""
    mock_manager.restart_unhealthy_modules.return_value = ['unhealthy_module']
    
    with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=mock_manager):
        response = client.post('/mcp/restart-unhealthy')
        
        assert response.status_code == 200
        data = response.get_json()
        assert "Restarted unhealthy modules" in data["message"]
        assert data["restarted"] == ['unhealthy_module']
        mock_manager.restart_unhealthy_modules.assert_called_once()


def test_management_ui_route(client):
    """Test management UI route."""
    with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=Mock()):
        response = client.get('/mcp/ui')
        
        assert response.status_code == 200
        assert b'MCP Module Management' in response.data
        assert b'<script>' in response.data  # Should contain JavaScript
        assert b'refreshStatus()' in response.data


def test_routes_with_no_manager(client):
    """Test various routes when manager is not available."""
    with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=None):
        # Test various routes
        routes_to_test = [
            ('/mcp/start/test_module', 'POST'),
            ('/mcp/stop/test_module', 'POST'),
            ('/mcp/restart/test_module', 'POST'),
            ('/mcp/health/test_module', 'GET'),
            ('/mcp/health', 'GET'),
            ('/mcp/start-all', 'POST'),
            ('/mcp/stop-all', 'POST'),
            ('/mcp/restart-unhealthy', 'POST'),
        ]
        
        for route, method in routes_to_test:
            if method == 'POST':
                response = client.post(route)
            else:
                response = client.get(route)
            
            assert response.status_code == 500
            data = response.get_json()
            assert "MCP manager not initialized" in data["error"]


if __name__ == "__main__":
    pytest.main([__file__])