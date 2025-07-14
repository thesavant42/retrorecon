# MCP Module Management

This document describes the centralized MCP (Model Context Protocol) module management system implemented in RetroRecon.

## Overview

The MCP module management system provides centralized control over all MCP modules, allowing for dynamic initialization, monitoring, and lifecycle management. It includes both CLI and web-based management interfaces.

## Features

### Core Management Features
- **Centralized lifecycle management** - Start, stop, restart modules from a single interface
- **Configuration-driven design** - All modules configured via `mcp_servers.json`
- **Lazy loading support** - Modules can be started on-demand
- **Retry logic** - Configurable retry attempts with delays for failed module starts
- **Health checking** - Monitor module health and automatically restart unhealthy modules
- **Error handling** - Robust error handling with detailed logging

### Management Interfaces
- **CLI Interface** - Command-line tool for server administration
- **Web Interface** - Browser-based management UI
- **API Endpoints** - RESTful API for programmatic access

## Configuration

Modules are configured in `mcp_servers.json`:

```json
[
  {
    "name": "memory",
    "enabled": true,
    "transport": "stdio",
    "command": ["basic-memory", "mcp", "--transport", "stdio"],
    "lazy_start": false,
    "retry": {
      "attempts": 3,
      "delay": 2
    }
  },
  {
    "name": "fetch",
    "enabled": true,
    "transport": "sse",
    "url": "http://localhost:3000/sse",
    "lazy_start": true,
    "retry": {
      "attempts": 5,
      "delay": 3
    },
    "health_check_url": "http://localhost:3000/health"
  }
]
```

### Configuration Options

- `name`: Unique identifier for the module
- `enabled`: Whether the module should be available
- `transport`: Communication method ("stdio", "sse", "http")
- `command`: Command to execute (for stdio transport)
- `url`: Connection URL (for sse/http transport)
- `lazy_start`: Start module only when first accessed
- `retry`: Retry configuration with `attempts` and `delay` (seconds)
- `health_check_url`: Optional URL for health checking

## CLI Interface

The CLI tool (`mcp_cli.py`) provides command-line access to module management:

```bash
# Show module status
python mcp_cli.py status
python mcp_cli.py status --json

# Start/stop/restart modules
python mcp_cli.py start memory
python mcp_cli.py stop memory
python mcp_cli.py restart memory

# Health checking
python mcp_cli.py health memory
python mcp_cli.py health  # all modules

# Bulk operations
python mcp_cli.py start-all
python mcp_cli.py stop-all
python mcp_cli.py restart-unhealthy

# With custom database path
python mcp_cli.py --db-path /path/to/db.sqlite status
```

## Web Interface

Access the web management interface at: `http://localhost:5000/mcp/ui`

The interface provides:
- Real-time module status display
- One-click start/stop/restart actions
- Health checking controls
- Bulk operation buttons
- Error message display

## API Endpoints

### Module Status
- `GET /mcp/status` - Get status of all modules
- `GET /mcp/health` - Check health of all running modules
- `GET /mcp/health/<module_name>` - Check health of specific module

### Module Control
- `POST /mcp/start/<module_name>` - Start a module
- `POST /mcp/stop/<module_name>` - Stop a module
- `POST /mcp/restart/<module_name>` - Restart a module

### Bulk Operations
- `POST /mcp/start-all` - Start all enabled modules
- `POST /mcp/stop-all` - Stop all modules
- `POST /mcp/restart-unhealthy` - Restart unhealthy modules

## Module Status Information

Each module provides the following status information:

```json
{
  "name": "memory",
  "enabled": true,
  "running": false,
  "transport": "stdio",
  "last_started": 1234567890.0,
  "last_error": "Command not found: basic-memory",
  "health_check_url": null,
  "tools": ["list_tables", "execute_sql"]
}
```

## Error Handling and Retry Logic

The system implements robust error handling:

1. **FileNotFoundError** - Module command not found (no retry)
2. **Connection errors** - Retried according to module configuration
3. **Health check failures** - Module marked as unhealthy
4. **Timeout errors** - Configurable timeout with retry

## Cross-Machine Support

The system supports cross-machine setups:
- Modules can connect to remote services via URL
- Centralized logging across all modules
- Health checks work with remote endpoints
- Configuration supports different transport types

## Migration from Manual Management

The centralized system maintains backward compatibility:
- Existing modules continue to work
- Configuration is additive (new fields optional)
- Old manual start/stop methods still functional
- Gradual migration path available

## Troubleshooting

### Common Issues

1. **Module won't start**
   - Check if command exists in PATH
   - Verify configuration syntax
   - Review retry settings

2. **Health check failures**
   - Ensure module is properly initialized
   - Check network connectivity for remote modules
   - Review module-specific logs

3. **Performance issues**
   - Adjust retry delays
   - Use lazy loading for infrequently used modules
   - Monitor resource usage

### Debug Commands

```bash
# Check module configuration
python mcp_cli.py status --json

# Test health checking
python mcp_cli.py health

# View detailed logs
tail -f app.log | grep mcp_manager
```

## Best Practices

1. **Configuration**
   - Use lazy loading for optional modules
   - Set appropriate retry limits
   - Configure health check URLs where possible

2. **Monitoring**
   - Regularly check module health
   - Monitor logs for recurring errors
   - Use the web interface for real-time status

3. **Maintenance**
   - Restart unhealthy modules periodically
   - Update module configurations as needed
   - Test configuration changes in development first

## Future Enhancements

Planned improvements include:
- Scheduled health checks
- Module dependency management
- Configuration validation
- Performance metrics
- Advanced logging integration