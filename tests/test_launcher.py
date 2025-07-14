"""
Test the launcher module functionality.
"""

import os
import sys
import json
import tempfile
import subprocess
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrorecon.launcher import (
    run_git_pull,
    load_launch_config,
    setup_environment_variables,
    check_database_exists,
    check_venv_and_pip
)


def test_run_git_pull_success():
    """Test git pull with successful result."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Already up to date."
        mock_run.return_value.stderr = ""
        
        result = run_git_pull()
        
        assert result is True
        mock_run.assert_called_once_with(
            ['git', 'pull'],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            timeout=30
        )


def test_run_git_pull_failure():
    """Test git pull with failure."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "fatal: not a git repository"
        
        result = run_git_pull()
        
        assert result is False


def test_run_git_pull_not_found():
    """Test git pull when git command is not found."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError("git command not found")
        
        result = run_git_pull()
        
        assert result is False


def test_load_launch_config_exists():
    """Test loading configuration from existing file."""
    config_data = {
        "listen_addr": "0.0.0.0",
        "db_path": "/custom/path/test.db"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    try:
        # Mock getcwd to return the temp directory
        with patch('os.getcwd', return_value=os.path.dirname(temp_path)):
            with patch('os.path.join', return_value=temp_path):
                result = load_launch_config()
                
                assert result == config_data
    finally:
        os.unlink(temp_path)


def test_load_launch_config_not_exists():
    """Test loading configuration when file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch('os.getcwd', return_value=tmpdir):
            result = load_launch_config()
            
            assert result == {}


def test_load_launch_config_invalid_json():
    """Test loading configuration with invalid JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("invalid json content")
        temp_path = f.name
    
    try:
        with patch('os.getcwd', return_value=os.path.dirname(temp_path)):
            with patch('os.path.join', return_value=temp_path):
                result = load_launch_config()
                
                assert result == {}
    finally:
        os.unlink(temp_path)


def test_setup_environment_variables_defaults():
    """Test environment variable setup with defaults."""
    config = {}
    
    # Clear environment variables
    for var in ['RETRORECON_LOG_LEVEL', 'RETRORECON_LISTEN', 'RETRORECON_DB']:
        if var in os.environ:
            del os.environ[var]
    
    try:
        setup_environment_variables(config)
        
        assert os.environ['RETRORECON_LOG_LEVEL'] == 'DEBUG'
        assert os.environ['RETRORECON_LISTEN'] == '127.0.0.1'
        assert os.environ['RETRORECON_DB'].endswith('db/waybax.db')
    finally:
        # Clean up
        for var in ['RETRORECON_LOG_LEVEL', 'RETRORECON_LISTEN', 'RETRORECON_DB']:
            if var in os.environ:
                del os.environ[var]


def test_setup_environment_variables_from_config():
    """Test environment variable setup from config."""
    config = {
        "listen_addr": "0.0.0.0",
        "db_path": "/custom/path/test.db"
    }
    
    # Clear environment variables
    for var in ['RETRORECON_LOG_LEVEL', 'RETRORECON_LISTEN', 'RETRORECON_DB']:
        if var in os.environ:
            del os.environ[var]
    
    try:
        setup_environment_variables(config)
        
        assert os.environ['RETRORECON_LOG_LEVEL'] == 'DEBUG'
        assert os.environ['RETRORECON_LISTEN'] == '0.0.0.0'
        assert os.environ['RETRORECON_DB'] == '/custom/path/test.db'
    finally:
        # Clean up
        for var in ['RETRORECON_LOG_LEVEL', 'RETRORECON_LISTEN', 'RETRORECON_DB']:
            if var in os.environ:
                del os.environ[var]


def test_setup_environment_variables_existing():
    """Test that existing environment variables are not overwritten."""
    config = {
        "listen_addr": "0.0.0.0",
        "db_path": "/custom/path/test.db"
    }
    
    # Set existing environment variables
    os.environ['RETRORECON_LOG_LEVEL'] = 'INFO'
    os.environ['RETRORECON_LISTEN'] = '192.168.1.1'
    os.environ['RETRORECON_DB'] = '/existing/path/test.db'
    
    try:
        setup_environment_variables(config)
        
        # Should not overwrite existing values
        assert os.environ['RETRORECON_LOG_LEVEL'] == 'INFO'
        assert os.environ['RETRORECON_LISTEN'] == '192.168.1.1'
        assert os.environ['RETRORECON_DB'] == '/existing/path/test.db'
    finally:
        # Clean up
        for var in ['RETRORECON_LOG_LEVEL', 'RETRORECON_LISTEN', 'RETRORECON_DB']:
            if var in os.environ:
                del os.environ[var]


def test_check_database_exists_missing():
    """Test database existence check when file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nonexistent_path = os.path.join(tmpdir, "nonexistent.db")
        os.environ['RETRORECON_DB'] = nonexistent_path
        
        try:
            # Should not raise an exception, just print warning
            check_database_exists()
        finally:
            del os.environ['RETRORECON_DB']


def test_check_database_exists_present():
    """Test database existence check when file exists."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_path = f.name
    
    try:
        os.environ['RETRORECON_DB'] = temp_path
        
        # Should not raise an exception or print warning
        check_database_exists()
    finally:
        os.unlink(temp_path)
        del os.environ['RETRORECON_DB']


def test_check_venv_and_pip():
    """Test virtual environment and pip checking."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a fake requirements.txt
        requirements_path = os.path.join(tmpdir, 'requirements.txt')
        with open(requirements_path, 'w') as f:
            f.write('flask\nrequests\n')
        
        with patch('os.getcwd', return_value=tmpdir):
            # Should not raise an exception
            check_venv_and_pip()


if __name__ == '__main__':
    import pytest
    pytest.main([__file__])