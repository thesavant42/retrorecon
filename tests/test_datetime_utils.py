"""Test the datetime utilities module."""

import pytest
from retrorecon.datetime_utils import UTC, utc_now, utc_datetime, datetime, timezone


def test_utc_import():
    """Test that UTC is available from datetime_utils."""
    assert UTC is not None
    assert hasattr(UTC, 'utcoffset')
    assert UTC.utcoffset(None).total_seconds() == 0


def test_utc_now():
    """Test the utc_now helper function."""
    now = utc_now()
    assert now.tzinfo is not None
    assert now.tzinfo == UTC
    assert now.tzinfo.utcoffset(None).total_seconds() == 0


def test_utc_datetime():
    """Test the utc_datetime helper function."""
    dt = utc_datetime(2023, 1, 1, 12, 0, 0)
    assert dt.tzinfo is not None
    assert dt.tzinfo == UTC
    assert dt.year == 2023
    assert dt.month == 1
    assert dt.day == 1
    assert dt.hour == 12


def test_compatibility_with_standard_timezone():
    """Test that our UTC is compatible with timezone.utc."""
    assert UTC == timezone.utc