"""
Tests for MCP CLI interface.
"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from mcp_cli import main
import sys
from io import StringIO


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


def test_cli_status_command(mock_manager):
    """Test CLI status command."""
    with patch('mcp_cli.get_module_manager', return_value=mock_manager):
        with patch('sys.argv', ['mcp_cli.py', 'status']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = main()
                
                assert result == 0
                output = mock_stdout.getvalue()
                assert "test_module" in output
                assert "RUNNING" in output
                assert "stdio" in output


def test_cli_status_json_command(mock_manager):
    """Test CLI status command with JSON output."""
    with patch('mcp_cli.get_module_manager', return_value=mock_manager):
        with patch('sys.argv', ['mcp_cli.py', 'status', '--json']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = main()
                
                assert result == 0
                output = mock_stdout.getvalue()
                
                # Should be valid JSON
                json_data = json.loads(output)
                assert "test_module" in json_data
                assert json_data["test_module"]["running"] is True


def test_cli_start_command(mock_manager):
    """Test CLI start command."""
    with patch('mcp_cli.get_module_manager', return_value=mock_manager):
        with patch('sys.argv', ['mcp_cli.py', 'start', 'test_module']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = main()
                
                assert result == 0
                mock_manager.start.assert_called_once_with('test_module')
                output = mock_stdout.getvalue()
                assert "Started module: test_module" in output


def test_cli_stop_command(mock_manager):
    """Test CLI stop command."""
    with patch('mcp_cli.get_module_manager', return_value=mock_manager):
        with patch('sys.argv', ['mcp_cli.py', 'stop', 'test_module']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = main()
                
                assert result == 0
                mock_manager.stop.assert_called_once_with('test_module')
                output = mock_stdout.getvalue()
                assert "Stopped module: test_module" in output


def test_cli_restart_command(mock_manager):
    """Test CLI restart command."""
    with patch('mcp_cli.get_module_manager', return_value=mock_manager):
        with patch('sys.argv', ['mcp_cli.py', 'restart', 'test_module']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = main()
                
                assert result == 0
                mock_manager.restart.assert_called_once_with('test_module')
                output = mock_stdout.getvalue()
                assert "Restarted module: test_module" in output


def test_cli_health_single_module(mock_manager):
    """Test CLI health command for single module."""
    with patch('mcp_cli.get_module_manager', return_value=mock_manager):
        with patch('sys.argv', ['mcp_cli.py', 'health', 'test_module']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = main()
                
                assert result == 0
                mock_manager.check_module_health.assert_called_once_with('test_module')
                output = mock_stdout.getvalue()
                assert "test_module is healthy" in output


def test_cli_health_all_modules(mock_manager):
    """Test CLI health command for all modules."""
    with patch('mcp_cli.get_module_manager', return_value=mock_manager):
        with patch('sys.argv', ['mcp_cli.py', 'health']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = main()
                
                assert result == 0
                mock_manager.check_all_health.assert_called_once()
                output = mock_stdout.getvalue()
                assert "Health Status:" in output
                assert "test_module: healthy" in output


def test_cli_start_all_command(mock_manager):
    """Test CLI start-all command."""
    with patch('mcp_cli.get_module_manager', return_value=mock_manager):
        with patch('sys.argv', ['mcp_cli.py', 'start-all']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = main()
                
                assert result == 0
                mock_manager.start_all.assert_called_once()
                output = mock_stdout.getvalue()
                assert "Started all enabled modules" in output


def test_cli_stop_all_command(mock_manager):
    """Test CLI stop-all command."""
    with patch('mcp_cli.get_module_manager', return_value=mock_manager):
        with patch('sys.argv', ['mcp_cli.py', 'stop-all']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = main()
                
                assert result == 0
                mock_manager.stop_all.assert_called_once()
                output = mock_stdout.getvalue()
                assert "Stopped all modules" in output


def test_cli_restart_unhealthy_command(mock_manager):
    """Test CLI restart-unhealthy command."""
    mock_manager.restart_unhealthy_modules.return_value = ['unhealthy_module']
    
    with patch('mcp_cli.get_module_manager', return_value=mock_manager):
        with patch('sys.argv', ['mcp_cli.py', 'restart-unhealthy']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = main()
                
                assert result == 0
                mock_manager.restart_unhealthy_modules.assert_called_once()
                output = mock_stdout.getvalue()
                assert "Restarted unhealthy modules: unhealthy_module" in output


def test_cli_no_manager_error():
    """Test CLI when manager is not available."""
    with patch('mcp_cli.get_module_manager', return_value=None):
        with patch('sys.argv', ['mcp_cli.py', 'status']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = main()
                
                assert result == 1
                output = mock_stdout.getvalue()
                assert "MCP manager not initialized" in output


def test_cli_no_command():
    """Test CLI with no command."""
    with patch('sys.argv', ['mcp_cli.py']):
        with patch('sys.stdout', new_callable=StringIO):
            result = main()
            
            # Should show help and exit cleanly
            assert result is None  # No return value means normal exit


def test_cli_exception_handling(mock_manager):
    """Test CLI exception handling."""
    mock_manager.start.side_effect = Exception("Test error")
    
    with patch('mcp_cli.get_module_manager', return_value=mock_manager):
        with patch('sys.argv', ['mcp_cli.py', 'start', 'test_module']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                result = main()
                
                assert result == 1
                output = mock_stdout.getvalue()
                assert "Error: Test error" in output


def test_cli_with_db_path(mock_manager):
    """Test CLI with database path."""
    with patch('mcp_cli.get_module_manager', return_value=mock_manager):
        with patch('mcp_cli.start_mcp_sqlite') as mock_start:
            with patch('sys.argv', ['mcp_cli.py', '--db-path', '/test/path.db', 'status']):
                with patch('sys.stdout', new_callable=StringIO):
                    result = main()
                    
                    assert result == 0
                    mock_start.assert_called_once_with('/test/path.db')


if __name__ == "__main__":
    pytest.main([__file__])