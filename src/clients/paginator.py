"""EventsPaginator — асинхронный итератор для обхода cursor-based пагинации.

Использует EventsProviderClient.events() и проходит по всем страницам,
пока next не станет None.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from urllib.parse import parse_qs, urlparse

from src.clients.events_provider import _parse_event
from src.domain import Event

logger = logging.getLogger(__name__)


class EventsPaginator:
    """Асинхронный итератор по всем страницам событий.

    Пример:
        client = EventsProviderClient(...)
        async for event in EventsPaginator(client, changed_at="2000-01-01"):
            await repo.upsert(event)
    """

    def __init__(
        self,
        client,
        changed_at: str = "2000-01-01",
    ) -> None:
        self._client = client
        self._changed_at = changed_at
        self._cursor: str | None = None
        self._exhausted = False
        self._buffer: list[Event] = []
        self._buffer_idx = 0
        self._total_yielded = 0

    def __aiter__(self) -> AsyncIterator[Event]:
        return self

    async def __anext__(self) -> Event:
        # Если в буфере ещё есть элементы — отдаём следующий
        if self._buffer_idx < len(self._buffer):
            event = self._buffer[self._buffer_idx]
            self._buffer_idx += 1
            self._total_yielded += 1
            return event

        # Буфер исчерпан — если страницы тоже кончились, стоп
        if self._exhausted:
            raise StopAsyncIteration

        # Загружаем следующую страницу
        await self._fetch_next_page()

        # После загрузки опять проверяем буфер
        if self._buffer_idx < len(self._buffer):
            event = self._buffer[self._buffer_idx]
            self._buffer_idx += 1
            self._total_yielded += 1
            return event

        # Страница была пустой — заканчиваем
        raise StopAsyncIteration

    async def _fetch_next_page(self) -> None:
        """Запросить очередную страницу у клиента и заполнить буфер."""
        logger.debug(
            "Paginator: fetching page (cursor=%s, changed_at=%s)",
            self._cursor,
            self._changed_at,
        )

        data = await self._client.events(
            changed_at=self._changed_at,
            cursor=self._cursor,
        )

        results = data.get("results", [])
        self._buffer = [_parse_event(raw) for raw in results]
        self._buffer_idx = 0

        next_url = data.get("next")
        if next_url:
            self._cursor = _extract_cursor(next_url)
        else:
            self._cursor = None
            self._exhausted = True

    @property
    def total_yielded(self) -> int:
        """Количество событий, выданных итератором на данный момент."""
        return self._total_yielded


def _extract_cursor(url: str) -> str | None:
    """Извлечь параметр cursor из URL."""
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    return qs.get("cursor", [None])[0]
