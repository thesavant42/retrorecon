"""
Launcher module for RetroRecon application.

This module contains all the setup and configuration logic that was previously
in the launcher batch/shell scripts, including:
- Git pull at startup
- Configuration loading from launch_config.json
- Environment variable setup
- Database path validation and warnings
- Virtual environment/pip detection warnings
- Flask app startup
"""

import os
import sys
import json
import subprocess
import logging
from typing import Optional, Dict, Any


def run_git_pull() -> bool:
    """
    Run 'git pull' in the current directory.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        result = subprocess.run(
            ['git', 'pull'], 
            cwd=os.getcwd(),
            capture_output=True, 
            text=True, 
            timeout=30
        )
        if result.returncode == 0:
            print(f"Git pull successful: {result.stdout.strip()}")
            return True
        else:
            print(f"Git pull failed: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print("Git pull timed out after 30 seconds")
        return False
    except FileNotFoundError:
        print("Git command not found - skipping git pull")
        return False
    except Exception as e:
        print(f"Error running git pull: {e}")
        return False


def load_launch_config() -> Dict[str, Any]:
    """
    Load configuration from launch_config.json if it exists.
    
    Returns:
        Dict[str, Any]: Configuration dictionary, empty if file doesn't exist
    """
    config_path = os.path.join(os.getcwd(), 'launch_config.json')
    if not os.path.exists(config_path):
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"Loaded configuration from {config_path}")
        return config
    except json.JSONDecodeError as e:
        print(f"Error parsing launch_config.json: {e}")
        return {}
    except Exception as e:
        print(f"Error loading launch_config.json: {e}")
        return {}


def setup_environment_variables(config: Dict[str, Any]) -> None:
    """
    Set up environment variables based on configuration and defaults.
    
    Args:
        config: Configuration dictionary from launch_config.json
    """
    # Set RETRORECON_LOG_LEVEL with default
    if 'RETRORECON_LOG_LEVEL' not in os.environ:
        os.environ['RETRORECON_LOG_LEVEL'] = 'DEBUG'
    
    # Set RETRORECON_LISTEN with config or default
    listen_addr = config.get('listen_addr', '127.0.0.1')
    if 'RETRORECON_LISTEN' not in os.environ:
        os.environ['RETRORECON_LISTEN'] = listen_addr
    
    # Set RETRORECON_DB with config or default
    db_path = config.get('db_path', '')
    if not db_path:
        db_path = os.path.join(os.getcwd(), 'db', 'waybax.db')
    elif not os.path.isabs(db_path):
        # If path is relative, make it relative to current directory
        db_path = os.path.join(os.getcwd(), db_path)
    
    # Normalize path separators for the current OS
    db_path = os.path.normpath(db_path)
    
    if 'RETRORECON_DB' not in os.environ:
        os.environ['RETRORECON_DB'] = db_path
    
    print(f"Environment variables set:")
    print(f"  RETRORECON_LOG_LEVEL: {os.environ.get('RETRORECON_LOG_LEVEL')}")
    print(f"  RETRORECON_LISTEN: {os.environ.get('RETRORECON_LISTEN')}")
    print(f"  RETRORECON_DB: {os.environ.get('RETRORECON_DB')}")


def check_database_exists() -> None:
    """
    Check if the database file exists and warn if missing.
    """
    db_path = os.environ.get('RETRORECON_DB')
    if db_path and not os.path.exists(db_path):
        print(f"WARNING: Database not found at {db_path}")


def check_venv_and_pip() -> None:
    """
    Check if virtual environment and pip are properly set up.
    Print warnings if issues are detected, but do not auto-install.
    """
    # Check if we're in a virtual environment
    in_venv = (
        hasattr(sys, 'real_prefix') or 
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )
    
    if not in_venv:
        print("WARNING: Not running in a virtual environment")
        print("  Consider creating a virtual environment with: python -m venv venv")
        print("  Then activate it and install requirements with: pip install -r requirements.txt")
    
    # Check if requirements.txt exists
    requirements_path = os.path.join(os.getcwd(), 'requirements.txt')
    if not os.path.exists(requirements_path):
        print("WARNING: requirements.txt not found in current directory")
        return
    
    # Try to import some key dependencies to see if they're installed
    try:
        import flask
        import requests
        import sqlite3
    except ImportError as e:
        print(f"WARNING: Missing required dependencies: {e}")
        print(f"  Install with: pip install -r {requirements_path}")


def start_flask_app() -> None:
    """
    Start the Flask application by importing and running app.py.
    """
    try:
        # Import the Flask app and required functions
        from app import app
        from database import create_new_db, ensure_schema
        from mcp_manager import start_mcp_sqlite
        
        # Handle database initialization if needed
        env_db = os.environ.get('RETRORECON_DB')
        if env_db and app.config.get('DATABASE'):
            with app.app_context():
                if not os.path.exists(app.config['DATABASE']):
                    create_new_db(os.path.splitext(os.path.basename(env_db))[0])
                else:
                    ensure_schema()
            app.mcp_server = start_mcp_sqlite(app.config['DATABASE'])
        
        # Get host and port from environment
        host = os.environ.get('RETRORECON_LISTEN', '127.0.0.1')
        port = int(os.environ.get('RETRORECON_PORT', '5000'))
        
        print(f"Starting Flask app on {host}:{port}")
        
        # Run the app
        app.run(debug=True, host=host, port=port)
        
    except ImportError as e:
        print(f"Error importing Flask app: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting Flask app: {e}")
        sys.exit(1)


def main() -> None:
    """
    Main launcher function that orchestrates the startup process.
    """
    print("RetroRecon Launcher - Starting up...")
    
    # Step 1: Run git pull
    print("\n1. Running git pull...")
    run_git_pull()
    
    # Step 2: Load configuration
    print("\n2. Loading configuration...")
    config = load_launch_config()
    
    # Step 3: Set up environment variables
    print("\n3. Setting up environment variables...")
    setup_environment_variables(config)
    
    # Step 4: Check database existence
    print("\n4. Checking database...")
    check_database_exists()
    
    # Step 5: Check venv/pip setup
    print("\n5. Checking virtual environment and dependencies...")
    check_venv_and_pip()
    
    # Step 6: Start Flask app
    print("\n6. Starting Flask application...")
    start_flask_app()


if __name__ == '__main__':
    main()