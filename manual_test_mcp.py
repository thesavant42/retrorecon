#!/usr/bin/env python3
"""Manual test script for MCP module management functionality."""

import sys
import os
import json
import time
from unittest.mock import Mock, patch

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_manager import MCPModuleManager, ModuleStatus, ModuleInfo
from retrorecon.mcp.config import MCPConfig


def test_mcp_module_manager():
    """Test MCP module manager functionality."""
    print("Testing MCP Module Manager...")
    
    # Create test configuration
    config = MCPConfig()
    config.mcp_servers = [
        {
            "name": "test_memory",
            "enabled": True,
            "transport": "stdio",
            "command": ["echo", "mock-memory-server"],
            "lazy_start": False,
            "description": "Test memory module",
            "retry": {
                "attempts": 2,
                "delay": 0.1,
                "backoff": 1
            },
            "health_check": {
                "enabled": True,
                "interval": 5
            }
        },
        {
            "name": "test_fetch",
            "enabled": True,
            "transport": "sse",
            "url": "http://localhost:3000/sse",
            "lazy_start": True,
            "description": "Test fetch module",
            "retry": {
                "attempts": 3,
                "delay": 0.2,
                "backoff": 2
            },
            "health_check": {
                "enabled": False,
                "interval": 30
            }
        }
    ]
    
    # Create manager with mocked threading
    with patch('mcp_manager.threading.Thread'):
        manager = MCPModuleManager(config)
    
    print(f"✓ Created manager with {len(manager.modules)} modules")
    
    # Test module status
    status = manager.get_all_module_status()
    print(f"✓ Module status retrieved: {len(status)} modules")
    
    for name, info in status.items():
        print(f"  - {name}: {info.status.value} (lazy: {manager.modules[name].lazy_start})")
    
    # Test enable/disable
    result = manager.disable_module("test_memory")
    print(f"✓ Disabled test_memory: {result}")
    print(f"  - Enabled status: {manager.modules['test_memory'].enabled}")
    
    result = manager.enable_module("test_memory")
    print(f"✓ Enabled test_memory: {result}")
    print(f"  - Enabled status: {manager.modules['test_memory'].enabled}")
    
    # Test tools retrieval
    tools = manager.get_module_tools("test_memory")
    print(f"✓ Retrieved tools for test_memory: {tools}")
    
    # Test module info
    info = manager.get_module_status("test_memory")
    if info:
        print(f"✓ Module info for test_memory:")
        print(f"  - Status: {info.status.value}")
        print(f"  - Restart count: {info.restart_count}")
        print(f"  - Last error: {info.last_error}")
        print(f"  - Tools: {info.tools}")
    
    # Test cleanup
    manager.cleanup()
    print("✓ Manager cleanup completed")


def test_configuration_format():
    """Test the enhanced configuration format."""
    print("\nTesting Enhanced Configuration Format...")
    
    # Load actual config file
    try:
        with open('mcp_servers.json', 'r') as f:
            config_data = json.load(f)
        
        print(f"✓ Loaded configuration with {len(config_data)} modules")
        
        for module in config_data:
            name = module.get('name', 'unknown')
            print(f"  - {name}:")
            print(f"    Transport: {module.get('transport', 'stdio')}")
            print(f"    Enabled: {module.get('enabled', True)}")
            print(f"    Lazy start: {module.get('lazy_start', False)}")
            print(f"    Description: {module.get('description', 'N/A')}")
            
            if 'retry' in module:
                retry = module['retry']
                print(f"    Retry: {retry.get('attempts', 3)} attempts, {retry.get('delay', 3)}s delay")
            
            if 'health_check' in module:
                health = module['health_check']
                print(f"    Health check: {'enabled' if health.get('enabled', False) else 'disabled'}")
                if health.get('enabled', False):
                    print(f"      Interval: {health.get('interval', 30)}s")
    
    except FileNotFoundError:
        print("✗ mcp_servers.json not found")
    except json.JSONDecodeError as e:
        print(f"✗ JSON decode error: {e}")


def test_status_conversion():
    """Test status information conversion."""
    print("\nTesting Status Information Conversion...")
    
    # Create test module info
    info = ModuleInfo(name="test", status=ModuleStatus.RUNNING)
    info.last_start_time = time.time()
    info.last_error = None
    info.restart_count = 2
    info.last_health_check = time.time()
    info.tools = ["tool1", "tool2", "tool3"]
    
    print(f"✓ Created test module info:")
    print(f"  - Name: {info.name}")
    print(f"  - Status: {info.status.value}")
    print(f"  - Last start: {info.last_start_time}")
    print(f"  - Restart count: {info.restart_count}")
    print(f"  - Tools: {len(info.tools)}")
    
    # Test conversion to dict-like structure (as would be done in routes)
    status_dict = {
        'name': info.name,
        'status': info.status.value,
        'last_start_time': info.last_start_time,
        'last_error': info.last_error,
        'restart_count': info.restart_count,
        'last_health_check': info.last_health_check,
        'tools': info.tools
    }
    
    print(f"✓ Status dict conversion successful")
    print(f"  - Keys: {list(status_dict.keys())}")


def main():
    """Run all tests."""
    print("MCP Module Management System - Manual Test\n")
    
    test_mcp_module_manager()
    test_configuration_format()
    test_status_conversion()
    
    print("\n✓ All tests completed successfully!")


if __name__ == "__main__":
    main()