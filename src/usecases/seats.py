"""Use case для получения свободных мест с in-memory кэшем."""

from __future__ import annotations

import asyncio
import logging

from src.cache import seats_cache
from src.protocols import EventRepository, EventsProviderClient
from src.usecases.exceptions import EventNotFound, EventUnexpectedStatus

logger = logging.getLogger(__name__)

# Блокировка чтобы не гонять параллельные запросы в провайдер
# для одного и того же event_id.
_seats_locks: dict[str, asyncio.Lock] = {}


class GetSeatsUsecase:
    """Получить список свободных мест с кэшем 30 секунд."""

    def __init__(
        self,
        events: EventRepository,
        client: EventsProviderClient,
        cache_ttl: float = 30.0,
    ) -> None:
        self._events = events
        self._client = client
        self._cache_ttl = cache_ttl

    async def do(self, event_id: str) -> list[str] | None:
        # 1. Проверяем кэш
        cache_key = f"seats:{event_id}"
        cached = seats_cache.get(cache_key)
        if cached is not None:
            logger.debug("Seats cache hit for %s", event_id)
            return cached

        # 2. Проверяем событие в локальной БД
        event = await self._events.get(event_id)
        if event is None:
            raise EventNotFound

        if event.status.value != "published":
            raise EventUnexpectedStatus(event.status.value)

        # 3. Запрос к провайдеру (с блокировкой чтобы не дублировать)
        if event_id not in _seats_locks:
            _seats_locks[event_id] = asyncio.Lock()

        async with _seats_locks[event_id]:
            # Двойная проверка — могли успеть пока ждали лок
            cached = seats_cache.get(cache_key)
            if cached is not None:
                return cached

            seats = await self._client.fetch_seats(event_id)
            if seats is None:
                return None

            seats_cache.set(cache_key, seats)
            return seats


def invalidate_seats_cache(event_id: str) -> None:
    """Сбросить кэш мест для конкретного события."""
    seats_cache.invalidate(f"seats:{event_id}")
