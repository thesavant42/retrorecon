"""
MCP Module Management web interface.
"""
import json
from flask import Blueprint, request, jsonify, render_template_string
from mcp_manager import get_module_manager, start_mcp_sqlite
import app

bp = Blueprint('mcp_management', __name__, url_prefix='/mcp')


def _get_manager():
    """Get or create the MCP module manager instance."""
    manager = get_module_manager()
    if manager is None:
        start_mcp_sqlite(app.app.config.get('DATABASE'))
        manager = get_module_manager()
    return manager


@bp.route('/status', methods=['GET'])
def module_status():
    """Get the status of all MCP modules."""
    manager = _get_manager()
    if not manager:
        return jsonify({'error': 'MCP manager not initialized'}), 500
    
    status_dict = manager.get_all_module_status()
    
    # Convert to JSON-serializable format
    json_status = {}
    for name, status in status_dict.items():
        try:
            tools = getattr(status, 'tools', [])
            # Ensure tools is a list of strings
            if hasattr(tools, '__iter__') and not isinstance(tools, str):
                tools = list(tools)
            else:
                tools = []
            
            json_status[name] = {
                "name": getattr(status, 'name', name),
                "enabled": bool(getattr(status, 'enabled', False)),
                "running": bool(getattr(status, 'running', False)),
                "transport": str(getattr(status, 'transport', 'unknown')),
                "last_started": getattr(status, 'last_started', None),
                "last_error": getattr(status, 'last_error', None),
                "health_check_url": getattr(status, 'health_check_url', None),
                "tools": tools
            }
        except Exception as e:
            # Fallback for problematic status objects
            json_status[name] = {
                "name": name,
                "enabled": False,
                "running": False,
                "transport": "unknown",
                "last_started": None,
                "last_error": f"Error processing status: {e}",
                "health_check_url": None,
                "tools": []
            }
    
    return jsonify(json_status)


@bp.route('/start/<module_name>', methods=['POST'])
def start_module(module_name):
    """Start a specific module."""
    manager = _get_manager()
    if not manager:
        return jsonify({'error': 'MCP manager not initialized'}), 500
    
    try:
        manager.start(module_name)
        return jsonify({'message': f'Started module: {module_name}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/stop/<module_name>', methods=['POST'])
def stop_module(module_name):
    """Stop a specific module."""
    manager = _get_manager()
    if not manager:
        return jsonify({'error': 'MCP manager not initialized'}), 500
    
    try:
        manager.stop(module_name)
        return jsonify({'message': f'Stopped module: {module_name}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/restart/<module_name>', methods=['POST'])
def restart_module(module_name):
    """Restart a specific module."""
    manager = _get_manager()
    if not manager:
        return jsonify({'error': 'MCP manager not initialized'}), 500
    
    try:
        manager.restart(module_name)
        return jsonify({'message': f'Restarted module: {module_name}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/health/<module_name>', methods=['GET'])
def check_module_health(module_name):
    """Check the health of a specific module."""
    manager = _get_manager()
    if not manager:
        return jsonify({'error': 'MCP manager not initialized'}), 500
    
    try:
        is_healthy = manager.check_module_health(module_name)
        return jsonify({
            'module': module_name,
            'healthy': is_healthy
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/health', methods=['GET'])
def check_all_health():
    """Check the health of all modules."""
    manager = _get_manager()
    if not manager:
        return jsonify({'error': 'MCP manager not initialized'}), 500
    
    try:
        health_status = manager.check_all_health()
        return jsonify(health_status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/start-all', methods=['POST'])
def start_all_modules():
    """Start all enabled modules."""
    manager = _get_manager()
    if not manager:
        return jsonify({'error': 'MCP manager not initialized'}), 500
    
    try:
        manager.start_all()
        return jsonify({'message': 'Started all enabled modules'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/stop-all', methods=['POST'])
def stop_all_modules():
    """Stop all modules."""
    manager = _get_manager()
    if not manager:
        return jsonify({'error': 'MCP manager not initialized'}), 500
    
    try:
        manager.stop_all()
        return jsonify({'message': 'Stopped all modules'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/restart-unhealthy', methods=['POST'])
def restart_unhealthy_modules():
    """Restart all unhealthy modules."""
    manager = _get_manager()
    if not manager:
        return jsonify({'error': 'MCP manager not initialized'}), 500
    
    try:
        restarted = manager.restart_unhealthy_modules()
        return jsonify({
            'message': 'Restarted unhealthy modules',
            'restarted': restarted
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/ui', methods=['GET'])
def management_ui():
    """Simple web UI for MCP module management."""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MCP Module Management</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .module { border: 1px solid #ddd; padding: 10px; margin: 10px 0; border-radius: 5px; }
            .running { background-color: #d4edda; }
            .stopped { background-color: #f8d7da; }
            .disabled { background-color: #f6f6f6; }
            button { margin: 5px; padding: 5px 10px; }
            .status { margin: 10px 0; }
            .error { color: red; }
            .tools { font-size: 0.9em; color: #666; }
        </style>
    </head>
    <body>
        <h1>MCP Module Management</h1>
        
        <div class="controls">
            <button onclick="refreshStatus()">Refresh Status</button>
            <button onclick="startAll()">Start All</button>
            <button onclick="stopAll()">Stop All</button>
            <button onclick="restartUnhealthy()">Restart Unhealthy</button>
            <button onclick="checkHealth()">Check Health</button>
        </div>
        
        <div id="status"></div>
        <div id="modules"></div>

        <script>
            function refreshStatus() {
                fetch('/mcp/status')
                    .then(response => response.json())
                    .then(data => {
                        displayModules(data);
                    })
                    .catch(error => {
                        document.getElementById('status').innerHTML = '<p class="error">Error: ' + error + '</p>';
                    });
            }

            function displayModules(modules) {
                const container = document.getElementById('modules');
                container.innerHTML = '';
                
                for (const [name, module] of Object.entries(modules)) {
                    const div = document.createElement('div');
                    div.className = 'module ' + (module.running ? 'running' : (module.enabled ? 'stopped' : 'disabled'));
                    
                    const statusText = module.running ? 'RUNNING' : (module.enabled ? 'STOPPED' : 'DISABLED');
                    const toolsText = module.tools.length > 0 ? module.tools.join(', ') : 'No tools';
                    const errorText = module.last_error ? `<div class="error">Error: ${module.last_error}</div>` : '';
                    
                    div.innerHTML = `
                        <h3>${name} (${statusText})</h3>
                        <p>Transport: ${module.transport}</p>
                        <p class="tools">Tools: ${toolsText}</p>
                        ${errorText}
                        <button onclick="startModule('${name}')">Start</button>
                        <button onclick="stopModule('${name}')">Stop</button>
                        <button onclick="restartModule('${name}')">Restart</button>
                        <button onclick="checkModuleHealth('${name}')">Check Health</button>
                    `;
                    container.appendChild(div);
                }
            }

            function startModule(name) {
                fetch(`/mcp/start/${name}`, {method: 'POST'})
                    .then(response => response.json())
                    .then(data => {
                        showMessage(data.message || data.error);
                        refreshStatus();
                    });
            }

            function stopModule(name) {
                fetch(`/mcp/stop/${name}`, {method: 'POST'})
                    .then(response => response.json())
                    .then(data => {
                        showMessage(data.message || data.error);
                        refreshStatus();
                    });
            }

            function restartModule(name) {
                fetch(`/mcp/restart/${name}`, {method: 'POST'})
                    .then(response => response.json())
                    .then(data => {
                        showMessage(data.message || data.error);
                        refreshStatus();
                    });
            }

            function startAll() {
                fetch('/mcp/start-all', {method: 'POST'})
                    .then(response => response.json())
                    .then(data => {
                        showMessage(data.message || data.error);
                        refreshStatus();
                    });
            }

            function stopAll() {
                fetch('/mcp/stop-all', {method: 'POST'})
                    .then(response => response.json())
                    .then(data => {
                        showMessage(data.message || data.error);
                        refreshStatus();
                    });
            }

            function restartUnhealthy() {
                fetch('/mcp/restart-unhealthy', {method: 'POST'})
                    .then(response => response.json())
                    .then(data => {
                        showMessage(data.message + (data.restarted.length > 0 ? ': ' + data.restarted.join(', ') : ''));
                        refreshStatus();
                    });
            }

            function checkHealth() {
                fetch('/mcp/health')
                    .then(response => response.json())
                    .then(data => {
                        const healthStatus = Object.entries(data).map(([name, healthy]) => `${name}: ${healthy ? 'healthy' : 'unhealthy'}`).join(', ');
                        showMessage('Health Status: ' + healthStatus);
                    });
            }

            function checkModuleHealth(name) {
                fetch(`/mcp/health/${name}`)
                    .then(response => response.json())
                    .then(data => {
                        showMessage(`${name} is ${data.healthy ? 'healthy' : 'unhealthy'}`);
                    });
            }

            function showMessage(message) {
                const statusDiv = document.getElementById('status');
                statusDiv.innerHTML = '<p>' + message + '</p>';
                setTimeout(() => statusDiv.innerHTML = '', 3000);
            }

            // Initial load
            refreshStatus();
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)