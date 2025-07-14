"""Tests for MCP management routes."""

import pytest
import json
from unittest.mock import Mock, patch
from mcp_manager import ModuleStatus, ModuleInfo


class TestMCPManagementRoutes:
    """Test MCP management HTTP routes."""
    
    @pytest.fixture
    def app(self):
        """Create a test Flask app."""
        from flask import Flask
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        # Import the blueprint inside the fixture to avoid circular imports
        from retrorecon.routes.mcp_management import bp
        app.register_blueprint(bp)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return app.test_client()
    
    def test_get_status_no_manager(self, client):
        """Test status endpoint when no manager is available."""
        with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=None):
            response = client.get('/mcp/status')
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
            assert 'not initialized' in data['error']
    
    def test_get_status_success(self, client):
        """Test successful status retrieval."""
        # Mock manager and status
        mock_manager = Mock()
        mock_info = ModuleInfo(name="test", status=ModuleStatus.RUNNING)
        mock_info.last_start_time = 1234567890.0
        mock_info.last_error = None
        mock_info.restart_count = 2
        mock_info.last_health_check = 1234567891.0
        mock_info.tools = ["tool1", "tool2"]
        
        mock_manager.get_all_module_status.return_value = {"test": mock_info}
        mock_manager.modules = {"test": Mock(description="Test module")}
        
        with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=mock_manager):
            response = client.get('/mcp/status')
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert 'test' in data
            module_data = data['test']
            assert module_data['name'] == 'test'
            assert module_data['status'] == 'running'
            assert module_data['last_start_time'] == 1234567890.0
            assert module_data['last_error'] is None
            assert module_data['restart_count'] == 2
            assert module_data['last_health_check'] == 1234567891.0
            assert module_data['tools'] == ["tool1", "tool2"]
            assert module_data['description'] == "Test module"
    
    def test_start_module_success(self, client):
        """Test successful module start."""
        mock_manager = Mock()
        mock_manager.modules = {"test": Mock()}
        mock_manager.start.return_value = True
        
        with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=mock_manager):
            response = client.post('/mcp/start/test')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'message' in data
            assert 'started successfully' in data['message']
            mock_manager.start.assert_called_once_with('test')
    
    def test_start_module_not_found(self, client):
        """Test starting non-existent module."""
        mock_manager = Mock()
        mock_manager.modules = {}
        
        with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=mock_manager):
            response = client.post('/mcp/start/nonexistent')
            assert response.status_code == 404
            data = json.loads(response.data)
            assert 'error' in data
            assert 'not found' in data['error']
    
    def test_start_module_failure(self, client):
        """Test failed module start."""
        mock_manager = Mock()
        mock_manager.modules = {"test": Mock()}
        mock_manager.start.return_value = False
        
        mock_info = ModuleInfo(name="test", status=ModuleStatus.FAILED)
        mock_info.last_error = "Connection failed"
        mock_manager.get_module_status.return_value = mock_info
        
        with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=mock_manager):
            response = client.post('/mcp/start/test')
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
            assert 'Connection failed' in data['error']
    
    def test_stop_module_success(self, client):
        """Test successful module stop."""
        mock_manager = Mock()
        mock_manager.modules = {"test": Mock()}
        mock_manager.stop.return_value = True
        
        with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=mock_manager):
            response = client.post('/mcp/stop/test')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'message' in data
            assert 'stopped successfully' in data['message']
            mock_manager.stop.assert_called_once_with('test')
    
    def test_stop_module_failure(self, client):
        """Test failed module stop."""
        mock_manager = Mock()
        mock_manager.modules = {"test": Mock()}
        mock_manager.stop.return_value = False
        
        with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=mock_manager):
            response = client.post('/mcp/stop/test')
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
            assert 'Failed to stop' in data['error']
    
    def test_restart_module_success(self, client):
        """Test successful module restart."""
        mock_manager = Mock()
        mock_manager.modules = {"test": Mock()}
        mock_manager.restart.return_value = True
        
        with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=mock_manager):
            response = client.post('/mcp/restart/test')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'message' in data
            assert 'restarted successfully' in data['message']
            mock_manager.restart.assert_called_once_with('test')
    
    def test_restart_module_failure(self, client):
        """Test failed module restart."""
        mock_manager = Mock()
        mock_manager.modules = {"test": Mock()}
        mock_manager.restart.return_value = False
        
        mock_info = ModuleInfo(name="test", status=ModuleStatus.FAILED)
        mock_info.last_error = "Restart failed"
        mock_manager.get_module_status.return_value = mock_info
        
        with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=mock_manager):
            response = client.post('/mcp/restart/test')
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
            assert 'Restart failed' in data['error']
    
    def test_enable_module_success(self, client):
        """Test successful module enable."""
        mock_manager = Mock()
        mock_manager.modules = {"test": Mock()}
        mock_manager.enable_module.return_value = True
        
        with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=mock_manager):
            response = client.post('/mcp/enable/test')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'message' in data
            assert 'enabled successfully' in data['message']
            mock_manager.enable_module.assert_called_once_with('test')
    
    def test_disable_module_success(self, client):
        """Test successful module disable."""
        mock_manager = Mock()
        mock_manager.modules = {"test": Mock()}
        mock_manager.disable_module.return_value = True
        
        with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=mock_manager):
            response = client.post('/mcp/disable/test')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'message' in data
            assert 'disabled successfully' in data['message']
            mock_manager.disable_module.assert_called_once_with('test')
    
    def test_get_module_tools_success(self, client):
        """Test successful module tools retrieval."""
        mock_manager = Mock()
        mock_manager.modules = {"test": Mock()}
        mock_manager.get_module_tools.return_value = ["tool1", "tool2"]
        
        with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=mock_manager):
            response = client.get('/mcp/tools/test')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['module'] == 'test'
            assert data['tools'] == ["tool1", "tool2"]
            mock_manager.get_module_tools.assert_called_once_with('test')
    
    def test_dashboard_endpoint(self, client):
        """Test dashboard endpoint."""
        # Mock the render_template to avoid template loading issues in tests
        with patch('retrorecon.routes.mcp_management.render_template') as mock_render:
            mock_render.return_value = 'Dashboard HTML'
            response = client.get('/mcp/dashboard')
            assert response.status_code == 200
            assert response.data == b'Dashboard HTML'
            mock_render.assert_called_once_with('mcp_dashboard.html')
    
    def test_no_manager_error_handling(self, client):
        """Test error handling when manager is not available."""
        endpoints = [
            ('/mcp/start/test', 'POST'),
            ('/mcp/stop/test', 'POST'),
            ('/mcp/restart/test', 'POST'),
            ('/mcp/enable/test', 'POST'),
            ('/mcp/disable/test', 'POST'),
            ('/mcp/tools/test', 'GET'),
        ]
        
        with patch('retrorecon.routes.mcp_management.get_module_manager', return_value=None):
            for endpoint, method in endpoints:
                if method == 'POST':
                    response = client.post(endpoint)
                else:
                    response = client.get(endpoint)
                
                assert response.status_code == 500
                data = json.loads(response.data)
                assert 'error' in data
                assert 'not initialized' in data['error']