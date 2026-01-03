# carbot/services/latest_store.py
from __future__ import annotations

import threading
import time
from typing import Generic, TypeVar

T = TypeVar("T")


class LatestStore(Generic[T]):
    """
    Thread-safe 'latest value' store with a monotonic-ish timestamp key.
    Consumers can either poll via get() or block via wait_newer().
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self._value: T | None = None
        self._timestamp_ns: int = 0

    def set(self, value: T, *, timestamp_ns: int) -> None:
        with self._cond:
            self._value = value
            self._timestamp_ns = int(timestamp_ns)
            self._cond.notify_all()

    def get(self) -> tuple[T | None, int]:
        with self._lock:
            return self._value, self._timestamp_ns

    def wait_newer(
        self,
        *,
        last_timestamp_ns: int,
        stop_event: threading.Event,
        timeout_s: float,
    ) -> tuple[T | None, int]:
        deadline = time.monotonic() + float(timeout_s)
        with self._cond:
            while not stop_event.is_set():
                v = self._value
                ts = self._timestamp_ns
                if v is not None and ts != last_timestamp_ns:
                    return v, ts

                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return None, last_timestamp_ns

                self._cond.wait(timeout=remaining)

            return None, last_timestamp_ns