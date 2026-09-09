"""SQLAlchemy-реализация TicketRepository."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.db import TicketRow
from src.domain import Ticket


class SqlTicketRepository:
    """Репозиторий билетов."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        event_id: str,
        ticket_id: str,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> Ticket:
        row = TicketRow(
            id=ticket_id,
            event_id=event_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            seat=seat,
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(row)
        await self._session.commit()
        return Ticket(
            id=row.id,
            event_id=row.event_id,
            first_name=row.first_name,
            last_name=row.last_name,
            email=row.email,
            seat=row.seat,
            created_at=row.created_at,
        )

    async def get(self, ticket_id: str) -> Ticket | None:
        row = await self._session.get(TicketRow, ticket_id)
        if row is None:
            return None
        return Ticket(
            id=row.id,
            event_id=row.event_id,
            first_name=row.first_name,
            last_name=row.last_name,
            email=row.email,
            seat=row.seat,
            created_at=row.created_at,
        )

    async def delete(self, ticket_id: str) -> None:
        row = await self._session.get(TicketRow, ticket_id)
        if row is not None:
            await self._session.delete(row)
            await self._session.commit()