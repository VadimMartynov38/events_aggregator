"""Роутер билетов — регистрация и отмена."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.events_provider import SeatAlreadyTaken
from src.db import get_session
from src.deps import get_events_repo, get_provider_client, get_seats_usecase, get_tickets_repo
from src.schemas import CancelResponseSchema, RegisterRequestSchema, RegisterResponseSchema
from src.usecases.exceptions import (
    EventNotFound,
    EventUnexpectedStatus,
    RegistrationDeadlinePassed,
    SeatNotAvailable,
    TicketNotFound,
)
from src.usecases.tickets import CancelTicketUsecase, CreateTicketUsecase

router = APIRouter(tags=["tickets"])


@router.post("/api/tickets", response_model=RegisterResponseSchema, status_code=201)
async def register(
    body: RegisterRequestSchema,
    session: AsyncSession = Depends(get_session),
):
    """Зарегистрироваться на событие.

    Валидирует данные, проверяет статус события и дедлайн,
    убеждается, что место свободно, отправляет запрос в
    Events Provider, сохраняет билет локально.
    """
    client = get_provider_client()
    events_repo = get_events_repo(session)
    tickets_repo = get_tickets_repo(session)
    seats_usecase = get_seats_usecase(session)

    usecase = CreateTicketUsecase(client, events_repo, tickets_repo, seats_usecase)

    try:
        ticket_id = await usecase.do(
            event_id=body.event_id,
            first_name=body.first_name,
            last_name=body.last_name,
            email=body.email,
            seat=body.seat,
        )
    except EventNotFound:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    except EventUnexpectedStatus as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RegistrationDeadlinePassed:
        raise HTTPException(status_code=400, detail="Дедлайн регистрации прошёл")
    except SeatNotAvailable as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SeatAlreadyTaken as e:
        raise HTTPException(status_code=400, detail=str(e))

    return RegisterResponseSchema(ticket_id=ticket_id)


@router.delete("/api/tickets/{ticket_id}", response_model=CancelResponseSchema)
async def cancel_registration(
    ticket_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Отменить регистрацию по ticket_id."""
    client = get_provider_client()
    tickets_repo = get_tickets_repo(session)
    usecase = CancelTicketUsecase(client, tickets_repo)

    try:
        result = await usecase.do(ticket_id)
    except TicketNotFound:
        raise HTTPException(status_code=404, detail="Билет не найден")
    except SeatAlreadyTaken as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return CancelResponseSchema(success=result)
