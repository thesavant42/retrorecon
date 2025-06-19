import threading
import logging
from collections import deque
from typing import Optional, Tuple

_STATUS_LOCK = threading.Lock()
_STATUS_QUEUE: deque[Tuple[str, str]] = deque()

logger = logging.getLogger(__name__)


def push_status(code: str, message: str = "") -> None:
    """Append a status event to the queue."""
    with _STATUS_LOCK:
        _STATUS_QUEUE.append((code, message))
        logger.debug("push_status queued %s: %s (len=%d)", code, message, len(_STATUS_QUEUE))


def pop_status() -> Optional[Tuple[str, str]]:
    """Pop the oldest status event or return ``None`` if empty."""
    with _STATUS_LOCK:
        if _STATUS_QUEUE:
            evt = _STATUS_QUEUE.popleft()
            logger.debug(
                "pop_status returning %s: %s (len=%d)",
                evt[0],
                evt[1],
                len(_STATUS_QUEUE),
            )
            return evt
    return None
