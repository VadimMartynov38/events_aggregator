"""Роутер свободных мест."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.deps import get_seats_usecase
from src.schemas import SeatsSchema
from src.usecases.exceptions import EventNotFound, EventUnexpectedStatus

router = APIRouter(prefix="/api/events", tags=["seats"])


@router.get("/{event_id}/seats/", response_model=SeatsSchema)
async def list_seats(
    event_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Получить список свободных мест (с кэшем 30 секунд).

    Только для опубликованных событий.
    """
    seats_usecase = get_seats_usecase(session)

    try:
        seats = await seats_usecase.do(event_id)
    except EventNotFound:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    except EventUnexpectedStatus as e:
        raise HTTPException(status_code=400, detail=str(e))

    if seats is None:
        raise HTTPException(status_code=404, detail="Места не найдены")

    return SeatsSchema(event_id=event_id, available_seats=seats)