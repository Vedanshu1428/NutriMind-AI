from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock
from typing import Any


@dataclass
class CacheEntry:
    value: Any
    expires_at: datetime


class TTLCache:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = timedelta(seconds=ttl_seconds)
        self._entries: dict[str, CacheEntry] = {}
        self._lock = Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._entries.get(key)
            if not entry:
                return None
            if entry.expires_at <= datetime.utcnow():
                self._entries.pop(key, None)
                return None
            return entry.value

    def set(self, key: str, value: Any) -> Any:
        with self._lock:
            self._entries[key] = CacheEntry(value=value, expires_at=datetime.utcnow() + self.ttl)
        return value

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._entries.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> None:
        with self._lock:
            for key in list(self._entries.keys()):
                if key.startswith(prefix):
                    self._entries.pop(key, None)


diet_plan_cache = TTLCache(ttl_seconds=60 * 30)
restaurant_cache = TTLCache(ttl_seconds=60 * 20)
analytics_cache = TTLCache(ttl_seconds=60 * 10)
notification_cache = TTLCache(ttl_seconds=60 * 2)
