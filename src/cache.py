"""Простой in-memory кэш с TTL для свободных мест."""

from __future__ import annotations

import time
from typing import Any


class TTLCache:
    """Кэш с временем жизни записей.

    Не потокобезопасен сам по себе — для async-окружения
    используется в связке с asyncio.Lock на уровне use case.
    """

    def __init__(self, ttl: float = 30.0) -> None:
        self._ttl = ttl
        self._store: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        expires_at = time.monotonic() + self._ttl
        self._store[key] = (value, expires_at)

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)


seats_cache = TTLCache(ttl=30.0)
