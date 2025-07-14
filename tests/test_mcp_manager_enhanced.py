"""Tests for the enhanced MCP module management system."""

import pytest
import time
import threading
from unittest.mock import Mock, MagicMock, patch
from mcp_manager import (
    MCPModuleManager, 
    ModuleSpec, 
    ModuleStatus, 
    RetryConfig, 
    HealthCheckConfig, 
    ModuleInfo
)
from retrorecon.mcp.config import MCPConfig


class TestRetryConfig:
    """Test RetryConfig dataclass."""
    
    def test_default_values(self):
        config = RetryConfig()
        assert config.attempts == 3
        assert config.delay == 3
        assert config.backoff == 2

    def test_custom_values(self):
        config = RetryConfig(attempts=5, delay=2, backoff=3)
        assert config.attempts == 5
        assert config.delay == 2
        assert config.backoff == 3


class TestHealthCheckConfig:
    """Test HealthCheckConfig dataclass."""
    
    def test_default_values(self):
        config = HealthCheckConfig()
        assert config.enabled is False
        assert config.interval == 30

    def test_custom_values(self):
        config = HealthCheckConfig(enabled=True, interval=60)
        assert config.enabled is True
        assert config.interval == 60


class TestModuleInfo:
    """Test ModuleInfo dataclass."""
    
    def test_default_values(self):
        info = ModuleInfo(name="test", status=ModuleStatus.STOPPED)
        assert info.name == "test"
        assert info.status == ModuleStatus.STOPPED
        assert info.last_start_time is None
        assert info.last_error is None
        assert info.restart_count == 0
        assert info.last_health_check is None
        assert info.tools == []


class TestMCPModuleManager:
    """Test enhanced MCPModuleManager functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = MCPConfig()
        self.config.mcp_servers = [
            {
                "name": "memory",
                "enabled": True,
                "transport": "stdio",
                "command": ["basic-memory", "mcp", "--transport", "stdio"],
                "lazy_start": False,
                "description": "Basic memory storage",
                "retry": {
                    "attempts": 3,
                    "delay": 1,
                    "backoff": 2
                },
                "health_check": {
                    "enabled": True,
                    "interval": 10
                }
            },
            {
                "name": "fetch",
                "enabled": True,
                "transport": "sse",
                "url": "http://localhost:3000/sse",
                "lazy_start": True,
                "description": "Fetch web content",
                "retry": {
                    "attempts": 5,
                    "delay": 2,
                    "backoff": 1
                },
                "health_check": {
                    "enabled": False,
                    "interval": 30
                }
            }
        ]

    def test_config_parsing(self):
        """Test configuration parsing."""
        with patch('mcp_manager.threading.Thread'):
            manager = MCPModuleManager(self.config)
        
        assert "memory" in manager.modules
        assert "fetch" in manager.modules
        
        memory_spec = manager.modules["memory"]
        assert memory_spec.name == "memory"
        assert memory_spec.enabled is True
        assert memory_spec.transport == "stdio"
        assert memory_spec.command == ["basic-memory", "mcp", "--transport", "stdio"]
        assert memory_spec.lazy_start is False
        assert memory_spec.description == "Basic memory storage"
        assert memory_spec.retry.attempts == 3
        assert memory_spec.retry.delay == 1
        assert memory_spec.retry.backoff == 2
        assert memory_spec.health_check.enabled is True
        assert memory_spec.health_check.interval == 10
        
        fetch_spec = manager.modules["fetch"]
        assert fetch_spec.name == "fetch"
        assert fetch_spec.enabled is True
        assert fetch_spec.transport == "sse"
        assert fetch_spec.url == "http://localhost:3000/sse"
        assert fetch_spec.lazy_start is True
        assert fetch_spec.description == "Fetch web content"
        assert fetch_spec.retry.attempts == 5
        assert fetch_spec.retry.delay == 2
        assert fetch_spec.retry.backoff == 1
        assert fetch_spec.health_check.enabled is False
        assert fetch_spec.health_check.interval == 30

    def test_module_info_initialization(self):
        """Test module info initialization."""
        with patch('mcp_manager.threading.Thread'):
            manager = MCPModuleManager(self.config)
        
        assert "memory" in manager.module_info
        assert "fetch" in manager.module_info
        
        memory_info = manager.module_info["memory"]
        assert memory_info.name == "memory"
        assert memory_info.status == ModuleStatus.STOPPED
        assert memory_info.last_start_time is None
        assert memory_info.last_error is None
        assert memory_info.restart_count == 0
        assert memory_info.last_health_check is None
        assert memory_info.tools == []

    @patch('mcp_manager.start_blocking_portal')
    @patch('mcp_manager.ClientSessionGroup')
    def test_successful_start(self, mock_session_group, mock_portal):
        """Test successful module start."""
        # Mock the portal and session group
        mock_portal_instance = Mock()
        mock_portal.return_value = mock_portal_instance
        
        mock_group = Mock()
        mock_group.tools = {"test_tool": Mock()}
        mock_session_group.return_value = mock_group
        
        # Mock the async context manager
        mock_portal_instance.call = Mock(return_value=mock_group)
        
        with patch('mcp_manager.threading.Thread'):
            manager = MCPModuleManager(self.config)
        
        # Test starting a module
        result = manager.start("memory")
        
        assert result is True
        assert manager.groups["memory"] is not None
        assert manager.portals["memory"] is not None
        
        memory_info = manager.module_info["memory"]
        assert memory_info.status == ModuleStatus.RUNNING
        assert memory_info.last_start_time is not None
        assert memory_info.last_error is None
        assert memory_info.tools == ["test_tool"]

    @patch('mcp_manager.start_blocking_portal')
    @patch('mcp_manager.ClientSessionGroup')
    def test_failed_start_with_retry(self, mock_session_group, mock_portal):
        """Test failed module start with retry logic."""
        # Mock the portal to raise an exception
        mock_portal_instance = Mock()
        mock_portal.return_value = mock_portal_instance
        mock_portal_instance.call = Mock(side_effect=Exception("Connection failed"))
        
        with patch('mcp_manager.threading.Thread'):
            manager = MCPModuleManager(self.config)
        
        # Reduce retry attempts for faster testing
        manager.modules["memory"].retry.attempts = 2
        manager.modules["memory"].retry.delay = 0.1
        
        start_time = time.time()
        result = manager.start("memory")
        end_time = time.time()
        
        assert result is False
        assert manager.groups["memory"] is None
        
        memory_info = manager.module_info["memory"]
        assert memory_info.status == ModuleStatus.FAILED
        assert memory_info.last_error == "Connection failed"
        
        # Check that retry delay was applied
        assert end_time - start_time >= 0.1

    @patch('mcp_manager.start_blocking_portal')
    @patch('mcp_manager.ClientSessionGroup')
    def test_stop_module(self, mock_session_group, mock_portal):
        """Test stopping a module."""
        # Set up a running module
        mock_portal_instance = Mock()
        mock_portal.return_value = mock_portal_instance
        
        mock_group = Mock()
        mock_group.tools = {"test_tool": Mock()}
        mock_portal_instance.call = Mock(return_value=mock_group)
        
        with patch('mcp_manager.threading.Thread'):
            manager = MCPModuleManager(self.config)
        
        # Start the module first
        manager.start("memory")
        assert manager.groups["memory"] is not None
        
        # Now stop it
        result = manager.stop("memory")
        
        assert result is True
        assert manager.groups["memory"] is None
        assert manager.portals["memory"] is None
        
        memory_info = manager.module_info["memory"]
        assert memory_info.status == ModuleStatus.STOPPED
        assert memory_info.tools == []

    @patch('mcp_manager.start_blocking_portal')
    @patch('mcp_manager.ClientSessionGroup')
    def test_restart_module(self, mock_session_group, mock_portal):
        """Test restarting a module."""
        # Set up a running module
        mock_portal_instance = Mock()
        mock_portal.return_value = mock_portal_instance
        
        mock_group = Mock()
        mock_group.tools = {"test_tool": Mock()}
        mock_portal_instance.call = Mock(return_value=mock_group)
        
        with patch('mcp_manager.threading.Thread'):
            manager = MCPModuleManager(self.config)
        
        # Start the module first
        manager.start("memory")
        
        initial_restart_count = manager.module_info["memory"].restart_count
        
        # Restart it
        result = manager.restart("memory")
        
        assert result is True
        assert manager.groups["memory"] is not None
        
        memory_info = manager.module_info["memory"]
        assert memory_info.status == ModuleStatus.RUNNING
        assert memory_info.restart_count == initial_restart_count + 1

    def test_enable_disable_module(self):
        """Test enabling and disabling modules."""
        with patch('mcp_manager.threading.Thread'):
            manager = MCPModuleManager(self.config)
        
        # Test disabling a module
        result = manager.disable_module("memory")
        assert result is True
        assert manager.modules["memory"].enabled is False
        
        # Test enabling a lazy-start module (should not try to start automatically)
        manager.modules["memory"].lazy_start = True
        result = manager.enable_module("memory")
        assert result is True
        assert manager.modules["memory"].enabled is True
        
        # Test enabling a non-lazy module with a mock start that succeeds
        manager.modules["memory"].lazy_start = False
        with patch.object(manager, 'start', return_value=True):
            result = manager.enable_module("memory")
            assert result is True
            assert manager.modules["memory"].enabled is True

    def test_get_module_status(self):
        """Test getting module status."""
        with patch('mcp_manager.threading.Thread'):
            manager = MCPModuleManager(self.config)
        
        status = manager.get_module_status("memory")
        assert status is not None
        assert status.name == "memory"
        assert status.status == ModuleStatus.STOPPED
        
        # Test non-existent module
        status = manager.get_module_status("non_existent")
        assert status is None

    def test_get_all_module_status(self):
        """Test getting all module statuses."""
        with patch('mcp_manager.threading.Thread'):
            manager = MCPModuleManager(self.config)
        
        all_status = manager.get_all_module_status()
        assert len(all_status) == 2
        assert "memory" in all_status
        assert "fetch" in all_status
        
        # Verify it's a copy, not the original
        all_status["memory"].status = ModuleStatus.RUNNING
        assert manager.module_info["memory"].status == ModuleStatus.STOPPED

    def test_get_module_tools(self):
        """Test getting module tools."""
        with patch('mcp_manager.threading.Thread'):
            manager = MCPModuleManager(self.config)
        
        # Initially no tools
        tools = manager.get_module_tools("memory")
        assert tools == []
        
        # Set some tools
        manager.module_info["memory"].tools = ["tool1", "tool2"]
        tools = manager.get_module_tools("memory")
        assert tools == ["tool1", "tool2"]
        
        # Test non-existent module
        tools = manager.get_module_tools("non_existent")
        assert tools == []

    def test_cleanup(self):
        """Test manager cleanup."""
        with patch('mcp_manager.threading.Thread') as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            manager = MCPModuleManager(self.config)
            
            # Test cleanup
            manager.cleanup()
            
            # Verify health check thread was stopped
            assert manager._health_check_stop.is_set()
            mock_thread_instance.join.assert_called_once_with(timeout=5)