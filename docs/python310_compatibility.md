# Python 3.10 Compatibility Guide

This document explains how to handle datetime.UTC compatibility between Python 3.10 and Python 3.11+.

## Problem

Python 3.11 introduced `datetime.UTC` as a convenient constant for the UTC timezone. However, this constant is not available in Python 3.10 and earlier versions, causing `ImportError` when trying to import it:

```python
# This fails on Python 3.10:
from datetime import datetime, UTC
```

## Solution

### Method 1: Use the provided datetime_utils module

The recommended approach is to import UTC from the `retrorecon.datetime_utils` module:

```python
from retrorecon.datetime_utils import UTC, utc_now, utc_datetime

# Use UTC timezone
now = utc_now()
dt = utc_datetime(2023, 1, 1, 12, 0, 0)
```

### Method 2: Implement the compatibility pattern directly

If you need to implement this pattern in your own code:

```python
# Python 3.10 compatibility pattern
try:
    from datetime import datetime, UTC
except ImportError:
    from datetime import datetime, timezone
    UTC = timezone.utc

# Now UTC works on both Python 3.10 and 3.11+
now = datetime.now(UTC)
```

## Migration from deprecated functions

Also replace deprecated datetime functions:

```python
# Old (deprecated):
dt = datetime.utcfromtimestamp(timestamp)

# New (recommended):
from retrorecon.datetime_utils import UTC
dt = datetime.fromtimestamp(timestamp, UTC)
```

## Testing

Run the compatibility tests to verify everything works:

```bash
python -m pytest tests/test_datetime_utc_compatibility.py
python -m pytest tests/test_datetime_utils.py
python test_python310_compatibility.py
```

## Files Changed

- `retrorecon/datetime_utils.py` - New compatibility module
- `layerslayer/client.py` - Fixed deprecated utcfromtimestamp usage
- `tests/test_datetime_utc_compatibility.py` - Compatibility tests
- `tests/test_datetime_utils.py` - Module tests
- `test_python310_compatibility.py` - Demonstration script