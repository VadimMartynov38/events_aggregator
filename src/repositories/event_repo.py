"""SQLAlchemy-реализация EventRepository."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import EventRow
from src.domain import Event, EventStatus, Place


class SqlEventRepository:
    """Репозиторий событий поверх SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, event_id: str) -> Event | None:
        row = await self._session.get(EventRow, event_id)
        if row is None:
            return None
        return _row_to_event(row)

    async def list_filtered(
        self,
        *,
        date_from: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Event], int]:
        query = select(EventRow)

        if date_from:
            query = query.where(func.date(EventRow.event_time) >= date_from)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self._session.execute(count_query)).scalar_one()

        offset = (page - 1) * page_size
        page_query = (
            query.order_by(EventRow.event_time)
            .limit(page_size)
            .offset(offset)
        )
        rows: Sequence[EventRow] = (
            (await self._session.execute(page_query)).scalars().all()
        )

        events = [_row_to_event(r) for r in rows]
        return events, total

    async def upsert_many(self, events: list[Event]) -> None:
        """Массово upsert-ить события (вставить или обновить)."""
        for event in events:
            existing = await self._session.get(EventRow, event.id)
            data = _event_to_dict(event)
            if existing:
                for key, val in data.items():
                    setattr(existing, key, val)
            else:
                self._session.add(EventRow(**data))
        await self._session.commit()

    async def get_max_changed_at(self) -> datetime | None:
        query = select(func.max(EventRow.changed_at))
        result = await self._session.execute(query)
        return result.scalar_one_or_none()


def _row_to_event(row: EventRow) -> Event:
    return Event(
        id=row.id,
        name=row.name,
        place=Place(
            id=row.place_id,
            name=row.place_name,
            city=row.place_city,
            address=row.place_address,
            seats_pattern=row.place_seats_pattern,
            changed_at=row.place_changed_at,
            created_at=row.place_created_at,
        ),
        event_time=row.event_time,
        registration_deadline=row.registration_deadline,
        status=EventStatus(row.status),
        number_of_visitors=row.number_of_visitors,
        changed_at=row.changed_at,
        created_at=row.created_at,
        status_changed_at=row.status_changed_at,
    )


def _event_to_dict(event: Event) -> dict:
    return {
        "id": event.id,
        "name": event.name,
        "place_id": event.place.id,
        "place_name": event.place.name,
        "place_city": event.place.city,
        "place_address": event.place.address,
        "place_seats_pattern": event.place.seats_pattern,
        "place_changed_at": event.place.changed_at,
        "place_created_at": event.place.created_at,
        "event_time": event.event_time,
        "registration_deadline": event.registration_deadline,
        "status": event.status.value,
        "number_of_visitors": event.number_of_visitors,
        "changed_at": event.changed_at,
        "created_at": event.created_at,
        "status_changed_at": event.status_changed_at,
    }
