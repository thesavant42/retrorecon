"""
Tests for MCP Module Manager enhancements.
"""
import json
import tempfile
import time
import pytest
from unittest.mock import Mock, patch, MagicMock
from mcp_manager import MCPModuleManager, ModuleSpec, ModuleStatus
from retrorecon.mcp.config import MCPConfig


@pytest.fixture
def test_config():
    """Create a test configuration with mock modules."""
    return MCPConfig(
        mcp_servers=[
            {
                "name": "test_stdio",
                "enabled": True,
                "transport": "stdio",
                "command": ["echo", "test"],
                "lazy_start": False,
                "retry": {"attempts": 3, "delay": 1}
            },
            {
                "name": "test_sse",
                "enabled": True,
                "transport": "sse",
                "url": "http://localhost:3000/sse",
                "lazy_start": True,
                "retry": {"attempts": 2, "delay": 0.5}
            },
            {
                "name": "test_disabled",
                "enabled": False,
                "transport": "stdio",
                "command": ["echo", "disabled"],
                "lazy_start": False
            }
        ]
    )


@pytest.fixture
def manager(test_config):
    """Create a test MCPModuleManager."""
    return MCPModuleManager(test_config)


def test_module_spec_creation(manager):
    """Test that ModuleSpec objects are created correctly."""
    assert len(manager.modules) == 3
    
    stdio_spec = manager.modules["test_stdio"]
    assert stdio_spec.name == "test_stdio"
    assert stdio_spec.enabled is True
    assert stdio_spec.transport == "stdio"
    assert stdio_spec.command == ["echo", "test"]
    assert stdio_spec.lazy_start is False
    assert stdio_spec.retry == {"attempts": 3, "delay": 1}
    
    sse_spec = manager.modules["test_sse"]
    assert sse_spec.name == "test_sse"
    assert sse_spec.enabled is True
    assert sse_spec.transport == "sse"
    assert sse_spec.url == "http://localhost:3000/sse"
    assert sse_spec.lazy_start is True
    assert sse_spec.retry == {"attempts": 2, "delay": 0.5}
    
    disabled_spec = manager.modules["test_disabled"]
    assert disabled_spec.name == "test_disabled"
    assert disabled_spec.enabled is False


def test_module_status_creation(manager):
    """Test that ModuleStatus objects are created correctly."""
    status = manager.get_module_status("test_stdio")
    assert status is not None
    assert status.name == "test_stdio"
    assert status.enabled is True
    assert status.running is False
    assert status.transport == "stdio"
    assert status.tools == []
    assert status.last_started is None
    assert status.last_error is None


def test_get_all_module_status(manager):
    """Test getting status for all modules."""
    all_status = manager.get_all_module_status()
    assert len(all_status) == 3
    assert "test_stdio" in all_status
    assert "test_sse" in all_status
    assert "test_disabled" in all_status
    
    for status in all_status.values():
        assert isinstance(status, ModuleStatus)


def test_get_module_status_nonexistent(manager):
    """Test getting status for non-existent module."""
    status = manager.get_module_status("nonexistent")
    assert status is None


@patch('mcp_manager.start_blocking_portal')
@patch('mcp_manager.ClientSessionGroup')
def test_start_module_success(mock_group_class, mock_portal, manager):
    """Test successful module start."""
    mock_portal_instance = Mock()
    mock_portal.return_value = mock_portal_instance
    
    mock_group = Mock()
    mock_group.tools = {"test_tool": Mock()}
    mock_group_class.return_value = mock_group
    
    mock_portal_instance.call.return_value = mock_group
    
    manager.start("test_stdio")
    
    # Check that the module was started
    assert manager.groups["test_stdio"] is not None
    assert manager.portals["test_stdio"] is not None
    assert "test_stdio" in manager.module_start_times
    assert "test_stdio" not in manager.module_last_errors


@patch('mcp_manager.start_blocking_portal')
@patch('mcp_manager.ClientSessionGroup')
def test_start_module_with_retry(mock_group_class, mock_portal, manager):
    """Test module start with retry logic."""
    mock_portal_instance = Mock()
    mock_portal.return_value = mock_portal_instance
    
    mock_group = Mock()
    mock_group.tools = {"test_tool": Mock()}
    mock_group_class.return_value = mock_group
    
    # First call fails, second succeeds
    mock_portal_instance.call.side_effect = [Exception("Connection failed"), mock_group]
    
    with patch('time.sleep') as mock_sleep:
        manager.start("test_stdio")
        
        # Should have retried once
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_with(1)  # retry delay from config


@patch('mcp_manager.start_blocking_portal')
@patch('mcp_manager.ClientSessionGroup')
def test_start_module_retry_exhausted(mock_group_class, mock_portal, manager):
    """Test module start when all retries are exhausted."""
    mock_portal_instance = Mock()
    mock_portal.return_value = mock_portal_instance
    
    # All calls fail
    mock_portal_instance.call.side_effect = Exception("Connection failed")
    
    with patch('time.sleep') as mock_sleep:
        manager.start("test_stdio")
        
        # Should have retried 2 times (3 attempts - 1 original = 2 retries)
        assert mock_sleep.call_count == 2
        
        # Module should not be started
        assert manager.groups["test_stdio"] is None
        assert "test_stdio" in manager.module_last_errors


def test_start_disabled_module(manager):
    """Test starting a disabled module."""
    manager.start("test_disabled")
    
    # Should not start
    assert manager.groups["test_disabled"] is None
    assert "test_disabled" not in manager.module_start_times


@patch('mcp_manager.start_blocking_portal')
@patch('mcp_manager.ClientSessionGroup')
def test_start_module_file_not_found(mock_group_class, mock_portal, manager):
    """Test starting a module with FileNotFoundError."""
    mock_portal_instance = Mock()
    mock_portal.return_value = mock_portal_instance
    mock_portal_instance.call.side_effect = FileNotFoundError("Command not found")
    
    manager.start("test_stdio")
    
    # Should not retry on FileNotFoundError
    assert manager.groups["test_stdio"] is None
    assert "test_stdio" in manager.module_last_errors
    assert "Command not found" in manager.module_last_errors["test_stdio"]


@patch('mcp_manager.start_blocking_portal')
@patch('mcp_manager.ClientSessionGroup')
def test_stop_module(mock_group_class, mock_portal, manager):
    """Test stopping a module."""
    # First start the module
    mock_portal_instance = Mock()
    mock_portal.return_value = mock_portal_instance
    
    mock_group = Mock()
    mock_group.tools = {}
    mock_group_class.return_value = mock_group
    mock_portal_instance.call.return_value = mock_group
    
    manager.start("test_stdio")
    
    # Now stop it
    manager.stop("test_stdio")
    
    # Should be stopped
    assert manager.groups["test_stdio"] is None
    assert manager.portals["test_stdio"] is None
    assert "test_stdio" not in manager.module_start_times


@patch('mcp_manager.start_blocking_portal')
@patch('mcp_manager.ClientSessionGroup')
def test_restart_module(mock_group_class, mock_portal, manager):
    """Test restarting a module."""
    mock_portal_instance = Mock()
    mock_portal.return_value = mock_portal_instance
    
    mock_group = Mock()
    mock_group.tools = {}
    mock_group_class.return_value = mock_group
    mock_portal_instance.call.return_value = mock_group
    
    # Start the module first
    manager.start("test_stdio")
    original_start_time = manager.module_start_times.get("test_stdio")
    
    # Small delay to ensure different timestamp
    time.sleep(0.001)
    
    # Restart it
    manager.restart("test_stdio")
    
    # Should be running with new start time
    assert manager.groups["test_stdio"] is not None
    new_start_time = manager.module_start_times.get("test_stdio")
    assert new_start_time != original_start_time


@patch('mcp_manager.start_blocking_portal')
@patch('mcp_manager.ClientSessionGroup')
def test_check_module_health(mock_group_class, mock_portal, manager):
    """Test module health checking."""
    mock_portal_instance = Mock()
    mock_portal.return_value = mock_portal_instance
    
    mock_group = Mock()
    mock_group.tools = {"test_tool": Mock()}
    mock_group_class.return_value = mock_group
    mock_portal_instance.call.return_value = mock_group
    
    # Start the module
    manager.start("test_stdio")
    
    # Health check should pass
    assert manager.check_module_health("test_stdio") is True
    
    # Simulate health check failure
    mock_group.tools = Mock()
    mock_group.tools.keys.side_effect = Exception("Health check failed")
    
    assert manager.check_module_health("test_stdio") is False
    assert "test_stdio" in manager.module_last_errors


def test_check_module_health_not_running(manager):
    """Test health check on non-running module."""
    assert manager.check_module_health("test_stdio") is False


@patch('mcp_manager.start_blocking_portal')
@patch('mcp_manager.ClientSessionGroup')
def test_check_all_health(mock_group_class, mock_portal, manager):
    """Test checking health of all modules."""
    mock_portal_instance = Mock()
    mock_portal.return_value = mock_portal_instance
    
    mock_group = Mock()
    mock_group.tools = {"test_tool": Mock()}
    mock_group_class.return_value = mock_group
    mock_portal_instance.call.return_value = mock_group
    
    # Start one module
    manager.start("test_stdio")
    
    health_status = manager.check_all_health()
    
    # Should only check running modules
    assert "test_stdio" in health_status
    assert "test_sse" not in health_status  # not running
    assert "test_disabled" not in health_status  # not running


@patch('mcp_manager.start_blocking_portal')
@patch('mcp_manager.ClientSessionGroup')
def test_restart_unhealthy_modules(mock_group_class, mock_portal, manager):
    """Test restarting unhealthy modules."""
    mock_portal_instance = Mock()
    mock_portal.return_value = mock_portal_instance
    
    mock_group = Mock()
    mock_group.tools = {"test_tool": Mock()}
    mock_group_class.return_value = mock_group
    mock_portal_instance.call.return_value = mock_group
    
    # Start module
    manager.start("test_stdio")
    
    # Make it unhealthy
    mock_group.tools = Mock()
    mock_group.tools.keys.side_effect = Exception("Health check failed")
    
    with patch.object(manager, 'restart') as mock_restart:
        restarted = manager.restart_unhealthy_modules()
        
        assert restarted == ["test_stdio"]
        mock_restart.assert_called_once_with("test_stdio")


def test_lazy_start_module(manager):
    """Test lazy starting of modules."""
    # get_group should start lazy modules
    with patch.object(manager, 'start') as mock_start:
        group = manager.get_group("test_sse")  # lazy_start=True
        mock_start.assert_called_once_with("test_sse")


def test_non_lazy_start_module(manager):
    """Test non-lazy modules don't auto-start in get_group."""
    with patch.object(manager, 'start') as mock_start:
        group = manager.get_group("test_stdio")  # lazy_start=False
        mock_start.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__])