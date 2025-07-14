#!/usr/bin/env python3
"""
Command-line interface for managing MCP modules.
"""
import argparse
import json
import sys
from typing import Dict, Any
from mcp_manager import get_module_manager, start_mcp_sqlite, stop_mcp_sqlite
from retrorecon.mcp.config import load_config


def print_status(status_dict: Dict[str, Any]) -> None:
    """Print module status in a formatted way."""
    if not status_dict:
        print("No modules configured.")
        return
    
    print(f"{'Module':<12} {'Status':<10} {'Transport':<10} {'Tools':<20} {'Last Error'}")
    print("-" * 80)
    
    for name, status in status_dict.items():
        running = getattr(status, 'running', False)
        enabled = getattr(status, 'enabled', False)
        transport = getattr(status, 'transport', 'unknown')
        tools = getattr(status, 'tools', [])
        last_error = getattr(status, 'last_error', None)
        
        status_str = "RUNNING" if running else ("ENABLED" if enabled else "DISABLED")
        tools_str = ", ".join(tools[:3]) + ("..." if len(tools) > 3 else "")
        error_str = last_error[:30] + "..." if last_error and len(last_error) > 30 else (last_error or "")
        
        print(f"{name:<12} {status_str:<10} {transport:<10} {tools_str:<20} {error_str}")


def main():
    parser = argparse.ArgumentParser(description="MCP Module Manager CLI")
    parser.add_argument("--db-path", help="Database path for MCP server")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show module status")
    status_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start a module")
    start_parser.add_argument("module", help="Module name to start")
    
    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop a module")
    stop_parser.add_argument("module", help="Module name to stop")
    
    # Restart command
    restart_parser = subparsers.add_parser("restart", help="Restart a module")
    restart_parser.add_argument("module", help="Module name to restart")
    
    # Health check command
    health_parser = subparsers.add_parser("health", help="Check module health")
    health_parser.add_argument("module", nargs="?", help="Module name (all if not specified)")
    
    # Start all command
    subparsers.add_parser("start-all", help="Start all enabled modules")
    
    # Stop all command
    subparsers.add_parser("stop-all", help="Stop all modules")
    
    # Restart unhealthy command
    subparsers.add_parser("restart-unhealthy", help="Restart unhealthy modules")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize MCP server if needed
    if args.db_path:
        start_mcp_sqlite(args.db_path)
    
    manager = get_module_manager()
    if not manager:
        print("Error: MCP manager not initialized. Use --db-path to specify a database.")
        return 1
    
    try:
        if args.command == "status":
            status_dict = manager.get_all_module_status()
            if args.json:
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
                
                try:
                    print(json.dumps(json_status, indent=2))
                except Exception as e:
                    print(f"Error serializing status to JSON: {e}")
                    return 1
            else:
                print_status(status_dict)
        
        elif args.command == "start":
            manager.start(args.module)
            print(f"Started module: {args.module}")
        
        elif args.command == "stop":
            manager.stop(args.module)
            print(f"Stopped module: {args.module}")
        
        elif args.command == "restart":
            manager.restart(args.module)
            print(f"Restarted module: {args.module}")
        
        elif args.command == "health":
            if args.module:
                is_healthy = manager.check_module_health(args.module)
                print(f"Module {args.module} is {'healthy' if is_healthy else 'unhealthy'}")
            else:
                health_status = manager.check_all_health()
                print("Health Status:")
                for name, is_healthy in health_status.items():
                    print(f"  {name}: {'healthy' if is_healthy else 'unhealthy'}")
        
        elif args.command == "start-all":
            manager.start_all()
            print("Started all enabled modules")
        
        elif args.command == "stop-all":
            manager.stop_all()
            print("Stopped all modules")
        
        elif args.command == "restart-unhealthy":
            restarted = manager.restart_unhealthy_modules()
            if restarted:
                print(f"Restarted unhealthy modules: {', '.join(restarted)}")
            else:
                print("No unhealthy modules found")
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())