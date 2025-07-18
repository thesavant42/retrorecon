"""
Datetime utilities with Python 3.10 compatibility.

This module provides UTC timezone compatibility between Python 3.10 and 3.11+.
In Python 3.11+, datetime.UTC is available, but in Python 3.10 and earlier,
we need to use timezone.utc instead.
"""

from datetime import datetime, timezone

# Python 3.10 compatibility for UTC timezone
try:
    from datetime import UTC
except ImportError:
    # Fallback for Python 3.10 and earlier
    UTC = timezone.utc

__all__ = ['UTC', 'datetime', 'timezone']


def utc_now():
    """Return current datetime in UTC timezone."""
    return datetime.now(UTC)


def utc_datetime(*args, **kwargs):
    """Create a datetime object in UTC timezone."""
    return datetime(*args, **kwargs, tzinfo=UTC)