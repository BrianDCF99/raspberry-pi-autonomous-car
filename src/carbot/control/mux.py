from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Generic, Optional, Protocol, TypeVar

T = TypeVar("T")


class Source(Protocol[T]):
    def latest(self) -> Optional[T]: ...


@dataclass(frozen=True, slots=True)
class SourceEntry(Generic[T]):
    source: Source[T]
    max_age_s: float  # if command older than this, treat as stale
    priority: int     # smaller = higher priority
    name: str = ""


class PriorityMux(Generic[T]):
    def __init__(self, entries: list[SourceEntry[T]]) -> None:
        self._entries = sorted(entries, key=lambda e: e.priority)

    def pick(self) -> Optional[T]:
        now = monotonic()
        for e in self._entries:
            cmd = e.source.latest()
            if cmd is None:
                continue
            ts = getattr(cmd, "ts", None)
            if ts is None:
                # if no ts field, treat as always fresh
                return cmd
            if (now - float(ts)) <= float(e.max_age_s):
                return cmd
        return None