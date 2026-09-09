"""Dependency Injection — фабрики для репозиториев и клиентов."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.events_provider import EventsProviderClient
from src.db import async_session_factory
from src.protocols import (
    EventRepository,
    EventsProviderClient as EventsProviderClientProto,
    SyncMetaRepository,
    TicketRepository,
)
from src.repositories.event_repo import SqlEventRepository
from src.repositories.sync_repo import SqlSyncMetaRepository
from src.repositories.ticket_repo import SqlTicketRepository
from src.usecases.seats import GetSeatsUsecase

_provider_client: EventsProviderClient | None = None


def get_provider_client() -> EventsProviderClientProto:
    global _provider_client
    if _provider_client is None:
        _provider_client = EventsProviderClient()
    return _provider_client


def get_events_repo(session: AsyncSession) -> EventRepository:
    return SqlEventRepository(session)


def get_tickets_repo(session: AsyncSession) -> TicketRepository:
    return SqlTicketRepository(session)


def get_sync_meta_repo(session: AsyncSession) -> SyncMetaRepository:
    return SqlSyncMetaRepository(session)


def get_seats_usecase(
    session: AsyncSession,
) -> GetSeatsUsecase:
    return GetSeatsUsecase(
        events=get_events_repo(session),
        client=get_provider_client(),
    )


async def close_provider_client() -> None:
    global _provider_client
    if _provider_client is not None:
        await _provider_client.close()
        _provider_client = None