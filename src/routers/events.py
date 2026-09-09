"""Роутер событий — список и детальная информация."""

from __future__ import annotations

from datetime import date
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.deps import get_events_repo
from src.domain import Event
from src.schemas import (
    EventDetailSchema,
    EventSchema,
    PaginatedEventsSchema,
    PlaceDetailSchema,
    PlaceSchema,
)
from src.usecases.events import GetEventUsecase, ListEventsUsecase
from src.usecases.exceptions import EventNotFound

router = APIRouter(prefix="/api/events", tags=["events"])


def _event_to_schema(event: Event) -> EventSchema:
    return EventSchema(
        id=event.id,
        name=event.name,
        place=PlaceSchema(
            id=event.place.id,
            name=event.place.name,
            city=event.place.city,
            address=event.place.address,
        ),
        event_time=event.event_time,
        registration_deadline=event.registration_deadline,
        status=event.status.value,
        number_of_visitors=event.number_of_visitors,
    )


def _event_to_detail(event: Event) -> EventDetailSchema:
    return EventDetailSchema(
        id=event.id,
        name=event.name,
        place=PlaceDetailSchema(
            id=event.place.id,
            name=event.place.name,
            city=event.place.city,
            address=event.place.address,
            seats_pattern=event.place.seats_pattern,
        ),
        event_time=event.event_time,
        registration_deadline=event.registration_deadline,
        status=event.status.value,
        number_of_visitors=event.number_of_visitors,
    )


@router.get("/", response_model=PaginatedEventsSchema)
async def list_events(
    date_from: date | None = Query(
        None, description="События от даты (YYYY-MM-DD)"
    ),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    session: AsyncSession = Depends(get_session),
):
    """Получить список событий из локальной БД.

    Фильтрация по дате на уровне SQL, пагинация page/page_size.
    """
    repo = get_events_repo(session)
    usecase = ListEventsUsecase(repo)

    events, total = await usecase.do(
        date_from=date_from,
        page=page,
        page_size=page_size,
    )

    base = "/api/events"
    params: dict = {"page_size": page_size}
    if date_from:
        params["date_from"] = date_from.isoformat()

    next_url = None
    if page * page_size < total:
        next_url = f"{base}?{urlencode({**params, 'page': page + 1})}"

    prev_url = None
    if page > 1:
        prev_url = f"{base}?{urlencode({**params, 'page': page - 1})}"

    return PaginatedEventsSchema(
        count=total,
        next=next_url,
        previous=prev_url,
        results=[_event_to_schema(e) for e in events],
    )


@router.get("/{event_id}/", response_model=EventDetailSchema)
async def get_event(
    event_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Получить детальную информацию о событии."""
    repo = get_events_repo(session)
    usecase = GetEventUsecase(repo)

    try:
        event = await usecase.do(event_id)
    except EventNotFound:
        raise HTTPException(status_code=404, detail="Событие не найдено")

    return _event_to_detail(event)
