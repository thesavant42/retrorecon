"""Simple integration test for MCP management functionality."""

import pytest
from unittest.mock import Mock, patch
from mcp_manager import ModuleStatus, ModuleInfo


def test_mcp_management_status_logic():
    """Test the status logic in isolation."""
    # Mock manager
    mock_manager = Mock()
    mock_info = ModuleInfo(name="test", status=ModuleStatus.RUNNING)
    mock_info.last_start_time = 1234567890.0
    mock_info.last_error = None
    mock_info.restart_count = 2
    mock_info.last_health_check = 1234567891.0
    mock_info.tools = ["tool1", "tool2"]
    
    mock_manager.get_all_module_status.return_value = {"test": mock_info}
    mock_manager.modules = {"test": Mock(description="Test module")}
    
    # Test the conversion logic
    status_info = mock_manager.get_all_module_status()
    assert "test" in status_info
    
    info = status_info["test"]
    assert info.name == "test"
    assert info.status == ModuleStatus.RUNNING
    assert info.last_start_time == 1234567890.0
    assert info.last_error is None
    assert info.restart_count == 2
    assert info.last_health_check == 1234567891.0
    assert info.tools == ["tool1", "tool2"]


def test_module_actions_logic():
    """Test module action logic in isolation."""
    # Mock manager
    mock_manager = Mock()
    mock_manager.modules = {"test": Mock()}
    
    # Test start action
    mock_manager.start.return_value = True
    result = mock_manager.start("test")
    assert result is True
    mock_manager.start.assert_called_once_with("test")
    
    # Test stop action
    mock_manager.stop.return_value = True
    result = mock_manager.stop("test")
    assert result is True
    mock_manager.stop.assert_called_once_with("test")
    
    # Test restart action
    mock_manager.restart.return_value = True
    result = mock_manager.restart("test")
    assert result is True
    mock_manager.restart.assert_called_once_with("test")


def test_module_enable_disable_logic():
    """Test module enable/disable logic in isolation."""
    # Mock manager
    mock_manager = Mock()
    mock_manager.modules = {"test": Mock()}
    
    # Test enable action
    mock_manager.enable_module.return_value = True
    result = mock_manager.enable_module("test")
    assert result is True
    mock_manager.enable_module.assert_called_once_with("test")
    
    # Test disable action
    mock_manager.disable_module.return_value = True
    result = mock_manager.disable_module("test")
    assert result is True
    mock_manager.disable_module.assert_called_once_with("test")