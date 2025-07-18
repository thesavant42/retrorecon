#!/usr/bin/env python3
"""
Test script to demonstrate Python 3.10 compatibility for datetime.UTC.

This script simulates the error that would occur on Python 3.10 and shows
how our compatibility solution works.
"""

import sys


def test_python_310_scenario():
    """Simulate the Python 3.10 scenario where UTC import fails."""
    print(f"Python version: {sys.version}")
    
    # Simulate the error case (commented out to avoid actual error)
    print("\n1. Testing the problematic import (would fail on Python 3.10):")
    print("   from datetime import datetime, UTC")
    try:
        from datetime import UTC as direct_utc
        print("   ✓ Direct UTC import succeeded (Python 3.11+)")
    except ImportError as e:
        print(f"   ✗ Direct UTC import failed: {e}")
    
    # Show the working solution
    print("\n2. Testing our compatibility solution:")
    print("   try:")
    print("       from datetime import UTC")
    print("   except ImportError:")
    print("       from datetime import timezone")
    print("       UTC = timezone.utc")
    
    try:
        from datetime import UTC
        print("   ✓ UTC available directly")
    except ImportError:
        from datetime import timezone
        UTC = timezone.utc
        print("   ✓ UTC created from timezone.utc (Python 3.10 fallback)")
    
    # Test using our datetime_utils module
    print("\n3. Testing our datetime_utils module:")
    from retrorecon.datetime_utils import UTC as utils_utc, utc_now
    
    now = utc_now()
    print(f"   ✓ Current UTC time: {now}")
    print(f"   ✓ Timezone: {now.tzinfo}")
    print(f"   ✓ UTC offset: {now.tzinfo.utcoffset(None)}")
    
    print("\n✓ All datetime UTC compatibility tests passed!")


if __name__ == "__main__":
    test_python_310_scenario()