"""MCP Module Management Routes."""

import logging
from flask import Blueprint, request, jsonify, render_template
from mcp_manager import get_module_manager, ModuleStatus

logger = logging.getLogger(__name__)

bp = Blueprint('mcp_management', __name__, url_prefix='/mcp')


@bp.route('/status', methods=['GET'])
def get_status():
    """Get status of all MCP modules."""
    manager = get_module_manager()
    if not manager:
        return jsonify({'error': 'MCP module manager not initialized'}), 500
    
    status_info = manager.get_all_module_status()
    status_dict = {}
    
    for name, info in status_info.items():
        status_dict[name] = {
            'name': info.name,
            'status': info.status.value,
            'last_start_time': info.last_start_time,
            'last_error': info.last_error,
            'restart_count': info.restart_count,
            'last_health_check': info.last_health_check,
            'tools': info.tools,
            'description': manager.modules[name].description if name in manager.modules else ""
        }
    
    return jsonify(status_dict)


@bp.route('/start/<module_name>', methods=['POST'])
def start_module(module_name):
    """Start a specific MCP module."""
    manager = get_module_manager()
    if not manager:
        return jsonify({'error': 'MCP module manager not initialized'}), 500
    
    if module_name not in manager.modules:
        return jsonify({'error': f'Module {module_name} not found'}), 404
    
    success = manager.start(module_name)
    if success:
        return jsonify({'message': f'Module {module_name} started successfully'})
    else:
        info = manager.get_module_status(module_name)
        error_msg = info.last_error if info else 'Unknown error'
        return jsonify({'error': f'Failed to start module {module_name}: {error_msg}'}), 500


@bp.route('/stop/<module_name>', methods=['POST'])
def stop_module(module_name):
    """Stop a specific MCP module."""
    manager = get_module_manager()
    if not manager:
        return jsonify({'error': 'MCP module manager not initialized'}), 500
    
    if module_name not in manager.modules:
        return jsonify({'error': f'Module {module_name} not found'}), 404
    
    success = manager.stop(module_name)
    if success:
        return jsonify({'message': f'Module {module_name} stopped successfully'})
    else:
        return jsonify({'error': f'Failed to stop module {module_name}'}), 500


@bp.route('/restart/<module_name>', methods=['POST'])
def restart_module(module_name):
    """Restart a specific MCP module."""
    manager = get_module_manager()
    if not manager:
        return jsonify({'error': 'MCP module manager not initialized'}), 500
    
    if module_name not in manager.modules:
        return jsonify({'error': f'Module {module_name} not found'}), 404
    
    success = manager.restart(module_name)
    if success:
        return jsonify({'message': f'Module {module_name} restarted successfully'})
    else:
        info = manager.get_module_status(module_name)
        error_msg = info.last_error if info else 'Unknown error'
        return jsonify({'error': f'Failed to restart module {module_name}: {error_msg}'}), 500


@bp.route('/enable/<module_name>', methods=['POST'])
def enable_module(module_name):
    """Enable a specific MCP module."""
    manager = get_module_manager()
    if not manager:
        return jsonify({'error': 'MCP module manager not initialized'}), 500
    
    if module_name not in manager.modules:
        return jsonify({'error': f'Module {module_name} not found'}), 404
    
    success = manager.enable_module(module_name)
    if success:
        return jsonify({'message': f'Module {module_name} enabled successfully'})
    else:
        return jsonify({'error': f'Failed to enable module {module_name}'}), 500


@bp.route('/disable/<module_name>', methods=['POST'])
def disable_module(module_name):
    """Disable a specific MCP module."""
    manager = get_module_manager()
    if not manager:
        return jsonify({'error': 'MCP module manager not initialized'}), 500
    
    if module_name not in manager.modules:
        return jsonify({'error': f'Module {module_name} not found'}), 404
    
    success = manager.disable_module(module_name)
    if success:
        return jsonify({'message': f'Module {module_name} disabled successfully'})
    else:
        return jsonify({'error': f'Failed to disable module {module_name}'}), 500


@bp.route('/tools/<module_name>', methods=['GET'])
def get_module_tools(module_name):
    """Get tools available from a specific module."""
    manager = get_module_manager()
    if not manager:
        return jsonify({'error': 'MCP module manager not initialized'}), 500
    
    if module_name not in manager.modules:
        return jsonify({'error': f'Module {module_name} not found'}), 404
    
    tools = manager.get_module_tools(module_name)
    return jsonify({'module': module_name, 'tools': tools})


@bp.route('/dashboard', methods=['GET'])
def dashboard():
    """Render the MCP management dashboard."""
    return render_template('mcp_dashboard.html')