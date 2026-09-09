"""Протоколы — контракты, от которых зависит бизнес-логика.

БЛ импортирует только протоколы. Конкретные реализации
прокидываются через DI.
"""

from __future__ import annotations

import typing
from datetime import date, datetime

from src.domain import Event, SyncMeta, Ticket


class EventsProviderClient(typing.Protocol):
    """Клиент стороннего Events Provider API."""

    async def events(
        self, changed_at: str, cursor: str | None = None
    ) -> dict: ...

    async def fetch_seats(self, event_id: str) -> list[str] | None: ...

    async def register(
        self,
        event_id: str,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> str: ...

    async def unregister(self, event_id: str, ticket_id: str) -> bool: ...


class EventRepository(typing.Protocol):
    """Репозиторий событий — работает с локальной БД."""

    async def get(self, event_id: str) -> Event | None: ...

    async def list_filtered(
        self,
        *,
        date_from: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Event], int]: ...

    async def upsert_many(self, events: list[Event]) -> None: ...

    async def get_max_changed_at(self) -> datetime | None: ...


class TicketRepository(typing.Protocol):
    """Репозиторий билетов."""

    async def create(
        self,
        event_id: str,
        ticket_id: str,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> Ticket: ...

    async def get(self, ticket_id: str) -> Ticket | None: ...

    async def delete(self, ticket_id: str) -> None: ...


class SyncMetaRepository(typing.Protocol):
    """Репозиторий метаданных синхронизации."""

    async def get(self) -> SyncMeta | None: ...

    async def update(
        self,
        last_sync_time: datetime,
        last_changed_at: datetime | None,
        sync_status: str,
        events_synced: int,
        error_message: str | None = None,
    ) -> None: ...
