import time as time_module
from typing import Generic, TypeVar

V = TypeVar("V")

MISSING = object()


class TTLCache(Generic[V]):
    def __init__(self, ttl_seconds: float):
        self._ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[float, V]] = {}

    def get(self, key: str):
        entry = self._store.get(key)
        if entry is None:
            return MISSING
        cached_at, value = entry
        if time_module.monotonic() - cached_at >= self._ttl_seconds:
            return MISSING
        return value

    def set(self, key: str, value: V) -> None:
        self._store[key] = (time_module.monotonic(), value)
