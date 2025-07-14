# MCP Module Management System

The MCP Module Management System provides centralized control over all MCP (Model Context Protocol) modules in the RetroRecon application. This system enables dynamic initialization, monitoring, and lifecycle management of modules.

## Features

### Centralized Management
- **Unified Interface**: Control all MCP modules from a single dashboard
- **Dynamic Loading**: Modules can be started, stopped, and restarted on-demand
- **Health Monitoring**: Automatic health checks with configurable intervals
- **Error Tracking**: Detailed error reporting and retry mechanisms

### Enhanced Configuration
The system uses an enhanced JSON configuration format (`mcp_servers.json`) that supports:

```json
{
  "name": "module_name",
  "enabled": true,
  "transport": "stdio|sse|http",
  "command": ["command", "args"],
  "url": "http://localhost:3000/sse",
  "lazy_start": true,
  "description": "Module description",
  "retry": {
    "attempts": 5,
    "delay": 3,
    "backoff": 2
  },
  "health_check": {
    "enabled": true,
    "interval": 30
  }
}
```

### Web Interface
Access the management dashboard at `/mcp/dashboard` to:
- View real-time module status
- Start, stop, and restart modules
- Enable and disable modules
- View available tools per module
- Monitor error messages and restart counts

### REST API
The system provides RESTful endpoints for programmatic access:

- `GET /mcp/status` - Get status of all modules
- `POST /mcp/start/<name>` - Start a module
- `POST /mcp/stop/<name>` - Stop a module
- `POST /mcp/restart/<name>` - Restart a module
- `POST /mcp/enable/<name>` - Enable a module
- `POST /mcp/disable/<name>` - Disable a module
- `GET /mcp/tools/<name>` - Get module tools

## Module Status
Each module can be in one of these states:
- **STOPPED**: Module is not running
- **STARTING**: Module is in the process of starting
- **RUNNING**: Module is active and healthy
- **FAILED**: Module has failed and needs attention

## Configuration Options

### Retry Configuration
- `attempts`: Number of retry attempts (default: 3)
- `delay`: Initial delay between retries in seconds (default: 3)
- `backoff`: Multiplier for exponential backoff (default: 2)

### Health Check Configuration
- `enabled`: Whether health checks are enabled (default: false)
- `interval`: Health check interval in seconds (default: 30)

### Transport Types
- **stdio**: Standard input/output transport for local executables
- **sse**: Server-Sent Events for HTTP-based modules
- **http**: HTTP transport for web-based modules

## Error Handling
The system includes robust error handling:
- **Automatic Retries**: Failed starts are retried with exponential backoff
- **Error Logging**: Detailed error messages are logged and displayed
- **Graceful Degradation**: Failed modules don't affect other modules
- **Recovery**: Modules can be restarted after failures

## Health Monitoring
- **Background Monitoring**: Health checks run in a separate thread
- **Configurable Intervals**: Set custom health check frequencies
- **Tool Availability**: Monitors available tools from each module
- **Automatic Recovery**: Can detect and restart failed modules

## Usage Examples

### Starting a Module
```bash
curl -X POST http://localhost:5000/mcp/start/memory
```

### Getting Module Status
```bash
curl http://localhost:5000/mcp/status
```

### Viewing Dashboard
Navigate to `http://localhost:5000/mcp/dashboard` in your browser.

## Troubleshooting

### Module Won't Start
1. Check the module's configuration in `mcp_servers.json`
2. Verify the command path or URL is correct
3. Check the application logs for detailed error messages
4. Ensure dependencies are installed

### Health Check Failures
1. Verify the module is actually running
2. Check network connectivity for remote modules
3. Adjust health check intervals if needed
4. Review module-specific requirements

### Performance Issues
1. Reduce health check frequency for stable modules
2. Use lazy loading for infrequently used modules
3. Monitor resource usage of individual modules
4. Consider disabling unused modules

## Integration with Existing Systems

The new system is fully backward compatible with existing MCP configurations. Existing modules will continue to work without modification, while new features are opt-in through configuration.

## Testing

The system includes comprehensive tests:
- Unit tests for core functionality
- Integration tests for API endpoints
- Manual testing scripts
- Mock modules for testing without dependencies

Run tests with:
```bash
python -m pytest tests/test_mcp_manager_enhanced.py -v
python -m pytest tests/test_mcp_management_integration.py -v
```

## Future Enhancements

Planned improvements include:
- Cross-machine module management
- Module dependency management
- Performance metrics collection
- Configuration validation
- Module marketplace/registry