"""Test datetime UTC compatibility between Python 3.10 and 3.11+."""

import sys
import pytest
from datetime import datetime, timezone


def test_utc_import_compatibility():
    """Test that UTC can be imported or created consistently across Python versions."""
    # This test verifies that we can get UTC timezone regardless of Python version
    
    # Method 1: Try importing UTC (Python 3.11+)
    try:
        from datetime import UTC
        utc_ref = UTC
    except ImportError:
        # Fallback for Python 3.10 and earlier
        utc_ref = timezone.utc
    
    # Verify we have a valid timezone
    assert utc_ref is not None
    assert hasattr(utc_ref, 'utcoffset')
    
    # Test that we can create datetime with this timezone
    now_utc = datetime.now(utc_ref)
    assert now_utc.tzinfo is not None
    assert now_utc.tzinfo.utcoffset(None).total_seconds() == 0


def test_timezone_utc_fallback():
    """Test the fallback pattern we'll use in the codebase."""
    # This is the pattern we'll implement to fix the issue
    try:
        from datetime import UTC
    except ImportError:
        from datetime import timezone
        UTC = timezone.utc
    
    # Verify UTC works
    now = datetime.now(UTC)
    assert now.tzinfo is not None
    assert now.tzinfo.utcoffset(None).total_seconds() == 0


def test_python_version_info():
    """Test to document Python version for debugging."""
    print(f"Python version: {sys.version}")
    print(f"Python version info: {sys.version_info}")
    
    # This test is informational to help understand the environment
    assert sys.version_info.major == 3