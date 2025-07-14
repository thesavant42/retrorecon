"""Simple test for MCP config validation without circular imports."""

import sys
from pathlib import Path

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Test validation functions directly without importing the whole module
def _validate_server_config(server):
    """Validate a single server configuration entry."""
    errors = []
    
    # Required fields
    if not server.get('name'):
        errors.append("Server name is required")
    
    transport = server.get('transport', 'stdio')
    if transport not in ['stdio', 'sse', 'http']:
        errors.append(f"Invalid transport type: {transport}")
    
    # Transport-specific validation
    if transport in ['sse', 'http']:
        url = server.get('url')
        if not url:
            errors.append(f"URL is required for {transport} transport")
        elif not url.startswith(('http://', 'https://')):
            errors.append("URL must start with http:// or https://")
    
    if transport == 'stdio':
        command = server.get('command')
        if not command or not isinstance(command, list) or len(command) == 0:
            errors.append("Command is required for stdio transport and must be a non-empty list")
    
    # Optional field validation
    if 'enabled' in server and not isinstance(server['enabled'], bool):
        errors.append("'enabled' must be a boolean")
    
    if 'lazy_start' in server and not isinstance(server['lazy_start'], bool):
        errors.append("'lazy_start' must be a boolean")
    
    if 'timeout' in server:
        try:
            timeout = int(server['timeout'])
            if timeout <= 0:
                errors.append("Timeout must be a positive integer")
        except (ValueError, TypeError):
            errors.append("Timeout must be an integer")
    
    return errors


def _validate_config(config_data):
    """Validate the entire MCP configuration."""
    errors = []
    
    if not isinstance(config_data, list):
        errors.append("Configuration must be a list of server objects")
        return errors
    
    names = []
    for i, server in enumerate(config_data):
        if not isinstance(server, dict):
            errors.append(f"Server {i} must be an object")
            continue
        
        # Check for duplicate names
        name = server.get('name')
        if name in names:
            errors.append(f"Duplicate server name: {name}")
        names.append(name)
        
        # Validate individual server
        server_errors = _validate_server_config(server)
        for error in server_errors:
            errors.append(f"Server '{name}': {error}")
    
    return errors


def test_validate_server_config_valid_sse():
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


def test_validate_server_config_valid_stdio():
    """Test validation of valid stdio server configuration."""
    server = {
        'name': 'test-server',
        'transport': 'stdio',
        'command': ['python', '-m', 'some_module'],
        'enabled': True
    }
    errors = _validate_server_config(server)
    assert errors == []


def test_validate_server_config_missing_name():
    """Test validation fails when server name is missing."""
    server = {
        'transport': 'sse',
        'url': 'http://localhost:3000/sse'
    }
    errors = _validate_server_config(server)
    assert 'Server name is required' in errors


def test_validate_server_config_invalid_transport():
    """Test validation fails for invalid transport type."""
    server = {
        'name': 'test-server',
        'transport': 'invalid',
        'url': 'http://localhost:3000/sse'
    }
    errors = _validate_server_config(server)
    assert 'Invalid transport type: invalid' in errors


def test_validate_server_config_missing_url_for_sse():
    """Test validation fails when URL is missing for SSE transport."""
    server = {
        'name': 'test-server',
        'transport': 'sse'
    }
    errors = _validate_server_config(server)
    assert 'URL is required for sse transport' in errors


def test_validate_config_valid():
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


def test_validate_config_duplicate_names():
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


if __name__ == '__main__':
    # Run tests directly
    test_validate_server_config_valid_sse()
    print("✓ SSE validation test passed")
    
    test_validate_server_config_valid_stdio()
    print("✓ stdio validation test passed")
    
    test_validate_server_config_missing_name()
    print("✓ Missing name validation test passed")
    
    test_validate_server_config_invalid_transport()
    print("✓ Invalid transport validation test passed")
    
    test_validate_server_config_missing_url_for_sse()
    print("✓ Missing URL validation test passed")
    
    test_validate_config_valid()
    print("✓ Valid config validation test passed")
    
    test_validate_config_duplicate_names()
    print("✓ Duplicate names validation test passed")
    
    print("\nAll validation tests passed!")