"""MCP configuration management routes."""

import json
import os
from typing import Dict, Any, List, Optional

from flask import Blueprint, request, jsonify, current_app
from retrorecon.mcp.config import load_config, MCPConfig


bp = Blueprint('mcp_config', __name__, url_prefix='/api/mcp')


def _get_config_file_path() -> str:
    """Get the path to the MCP configuration file."""
    config = load_config()
    path = config.servers_file or 'mcp_servers.json'
    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)
    return path


def _validate_server_config(server: Dict[str, Any]) -> List[str]:
    """Validate a single server configuration entry.
    
    Returns a list of error messages, empty if valid.
    """
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
    
    if 'sse_read_timeout' in server:
        try:
            sse_timeout = int(server['sse_read_timeout'])
            if sse_timeout <= 0:
                errors.append("SSE read timeout must be a positive integer")
        except (ValueError, TypeError):
            errors.append("SSE read timeout must be an integer")
    
    return errors


def _validate_config(config_data: List[Dict[str, Any]]) -> List[str]:
    """Validate the entire MCP configuration.
    
    Returns a list of error messages, empty if valid.
    """
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


@bp.route('/config', methods=['GET'])
def get_config():
    """Get the current MCP configuration."""
    try:
        config_file = _get_config_file_path()
        
        if not os.path.exists(config_file):
            return jsonify({'servers': []})
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return jsonify({'servers': config_data})
    
    except Exception as e:
        return jsonify({'error': f'Failed to read configuration: {str(e)}'}), 500


@bp.route('/config', methods=['POST'])
def update_config():
    """Update the MCP configuration."""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        servers = data.get('servers', [])
        
        # Validate configuration
        errors = _validate_config(servers)
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        config_file = _get_config_file_path()
        
        # Create backup of existing config
        backup_file = f"{config_file}.bak"
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                backup_data = f.read()
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(backup_data)
        
        # Write new configuration
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(servers, f, indent=2)
        
        # Reload MCP servers
        success = _reload_mcp_servers()
        
        if success:
            return jsonify({'message': 'Configuration updated successfully'})
        else:
            # Restore backup if reload failed
            if os.path.exists(backup_file):
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_data = f.read()
                with open(config_file, 'w', encoding='utf-8') as f:
                    f.write(backup_data)
            return jsonify({'error': 'Failed to reload MCP servers, configuration restored'}), 500
    
    except Exception as e:
        return jsonify({'error': f'Failed to update configuration: {str(e)}'}), 500


def _reload_mcp_servers() -> bool:
    """Reload MCP servers after configuration change.
    
    Returns True if successful, False otherwise.
    """
    try:
        # Import here to avoid circular import
        from mcp_manager import get_module_manager, ModuleSpec
        
        # Get the current module manager
        manager = get_module_manager()
        if manager:
            # Stop all current servers
            manager.stop_all()
            
            # Reload configuration
            config = load_config()
            
            # Update the manager with new configuration
            manager.cfg = config
            manager.modules = {}
            for mod in config.mcp_servers or []:
                try:
                    spec = ModuleSpec(**mod)
                except TypeError:
                    spec = ModuleSpec(
                        name=mod.get("name", ""),
                        transport=mod.get("transport", "stdio"),
                        command=mod.get("command"),
                        url=mod.get("url"),
                        headers=mod.get("headers"),
                        timeout=mod.get("timeout"),
                        sse_read_timeout=mod.get("sse_read_timeout"),
                        enabled=mod.get("enabled", True),
                        lazy_start=mod.get("lazy_start", False),
                        retry=mod.get("retry"),
                    )
                manager.modules[spec.name] = spec
            
            # Reset groups and portals
            manager.groups = {n: None for n in manager.modules}
            manager.portals = {n: None for n in manager.modules}
            manager.portal_cms = {n: None for n in manager.modules}
            
            # Start enabled servers
            manager.start_all()
            
        return True
    
    except Exception as e:
        current_app.logger.error(f"Failed to reload MCP servers: {e}")
        return False


@bp.route('/status', methods=['GET'])
def get_status():
    """Get the status of MCP servers."""
    try:
        # Import here to avoid circular import
        from mcp_manager import get_module_manager
        
        manager = get_module_manager()
        if not manager:
            return jsonify({'servers': []})
        
        servers = []
        for name, spec in manager.modules.items():
            group = manager.groups.get(name)
            status = {
                'name': name,
                'enabled': spec.enabled,
                'transport': spec.transport,
                'url': spec.url,
                'command': spec.command,
                'lazy_start': spec.lazy_start,
                'running': group is not None,
                'tools': list(group.tools.keys()) if group else []
            }
            servers.append(status)
        
        return jsonify({'servers': servers})
    
    except Exception as e:
        return jsonify({'error': f'Failed to get status: {str(e)}'}), 500