"""Use cases для работы со списком событий и одним событием."""

from __future__ import annotations

from datetime import date

from src.domain import Event
from src.protocols import EventRepository
from src.usecases.exceptions import EventNotFound


class ListEventsUsecase:
    """Получить отфильтрованный список событий из локальной БД."""

    def __init__(self, events: EventRepository) -> None:
        self._events = events

    async def do(
        self,
        *,
        date_from: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Event], int]:
        return await self._events.list_filtered(
            date_from=date_from,
            page=page,
            page_size=page_size,
        )


class GetEventUsecase:
    """Получить одно событие по ID из локальной БД."""

    def __init__(self, events: EventRepository) -> None:
        self._events = events

    async def do(self, event_id: str) -> Event:
        event = await self._events.get(event_id)
        if event is None:
            raise EventNotFound
        return event
