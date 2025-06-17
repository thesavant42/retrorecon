import threading
from collections import deque
from typing import Optional, Tuple

_STATUS_LOCK = threading.Lock()
_STATUS_QUEUE: deque[Tuple[str, str]] = deque()


def push_status(code: str, message: str = "") -> None:
    """Append a status event to the queue."""
    with _STATUS_LOCK:
        _STATUS_QUEUE.append((code, message))


def pop_status() -> Optional[Tuple[str, str]]:
    """Pop the oldest status event or return ``None`` if empty."""
    with _STATUS_LOCK:
        if _STATUS_QUEUE:
            return _STATUS_QUEUE.popleft()
    return None
