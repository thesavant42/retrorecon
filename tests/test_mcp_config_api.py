"""Tests for MCP configuration API endpoints."""

import json
import os
import tempfile
import pytest
from unittest.mock import patch, mock_open
import sys
from pathlib import Path

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Import the validation functions directly, avoiding circular imports
from retrorecon.routes.mcp_config import _validate_server_config, _validate_config, _get_config_file_path


class TestMCPConfigValidation:
    """Test MCP configuration validation functions."""
    
    def test_validate_server_config_valid_sse(self):
        """Test validation of valid SSE server configuration."""
        server = {
            'name': 'test-server',
            'transport': 'sse',
            'url': 'http://localhost:3000/sse',
            'enabled': True,
            'lazy_start': False
        }
        errors = _validate_server_config(server)
        assert errors == []
    
    def test_validate_server_config_valid_stdio(self):
        """Test validation of valid stdio server configuration."""
        server = {
            'name': 'test-server',
            'transport': 'stdio',
            'command': ['python', '-m', 'some_module'],
            'enabled': True
        }
        errors = _validate_server_config(server)
        assert errors == []
    
    def test_validate_server_config_missing_name(self):
        """Test validation fails when server name is missing."""
        server = {
            'transport': 'sse',
            'url': 'http://localhost:3000/sse'
        }
        errors = _validate_server_config(server)
        assert 'Server name is required' in errors
    
    def test_validate_server_config_invalid_transport(self):
        """Test validation fails for invalid transport type."""
        server = {
            'name': 'test-server',
            'transport': 'invalid',
            'url': 'http://localhost:3000/sse'
        }
        errors = _validate_server_config(server)
        assert 'Invalid transport type: invalid' in errors
    
    def test_validate_server_config_missing_url_for_sse(self):
        """Test validation fails when URL is missing for SSE transport."""
        server = {
            'name': 'test-server',
            'transport': 'sse'
        }
        errors = _validate_server_config(server)
        assert 'URL is required for sse transport' in errors
    
    def test_validate_server_config_invalid_url(self):
        """Test validation fails for invalid URL."""
        server = {
            'name': 'test-server',
            'transport': 'sse',
            'url': 'invalid-url'
        }
        errors = _validate_server_config(server)
        assert 'URL must start with http:// or https://' in errors
    
    def test_validate_server_config_missing_command_for_stdio(self):
        """Test validation fails when command is missing for stdio transport."""
        server = {
            'name': 'test-server',
            'transport': 'stdio'
        }
        errors = _validate_server_config(server)
        assert 'Command is required for stdio transport and must be a non-empty list' in errors
    
    def test_validate_server_config_invalid_timeout(self):
        """Test validation fails for invalid timeout."""
        server = {
            'name': 'test-server',
            'transport': 'sse',
            'url': 'http://localhost:3000/sse',
            'timeout': -1
        }
        errors = _validate_server_config(server)
        assert 'Timeout must be a positive integer' in errors
    
    def test_validate_config_valid(self):
        """Test validation of valid configuration."""
        config_data = [
            {
                'name': 'server1',
                'transport': 'sse',
                'url': 'http://localhost:3000/sse',
                'enabled': True
            },
            {
                'name': 'server2',
                'transport': 'stdio',
                'command': ['python', '-m', 'module'],
                'enabled': True
            }
        ]
        errors = _validate_config(config_data)
        assert errors == []
    
    def test_validate_config_duplicate_names(self):
        """Test validation fails for duplicate server names."""
        config_data = [
            {
                'name': 'server1',
                'transport': 'sse',
                'url': 'http://localhost:3000/sse'
            },
            {
                'name': 'server1',
                'transport': 'stdio',
                'command': ['python', '-m', 'module']
            }
        ]
        errors = _validate_config(config_data)
        assert 'Duplicate server name: server1' in errors
    
    def test_validate_config_not_list(self):
        """Test validation fails when config is not a list."""
        config_data = {'not': 'a list'}
        errors = _validate_config(config_data)
        assert 'Configuration must be a list of server objects' in errors


class TestMCPConfigHelpers:
    """Test MCP configuration helper functions."""
    
    @patch('retrorecon.routes.mcp_config.load_config')
    def test_get_config_file_path_default(self, mock_load_config):
        """Test getting default config file path."""
        mock_config = type('MockConfig', (), {})()
        mock_config.servers_file = None
        mock_load_config.return_value = mock_config
        
        path = _get_config_file_path()
        assert path == 'mcp_servers.json'
    
    @patch('retrorecon.routes.mcp_config.load_config')
    def test_get_config_file_path_custom(self, mock_load_config):
        """Test getting custom config file path."""
        mock_config = type('MockConfig', (), {})()
        mock_config.servers_file = 'custom_servers.json'
        mock_load_config.return_value = mock_config
        
        path = _get_config_file_path()
        assert path == 'custom_servers.json'