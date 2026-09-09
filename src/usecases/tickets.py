"""Use cases для регистрации и отмены регистрации."""

from __future__ import annotations

from datetime import UTC, datetime

from src.protocols import EventRepository, EventsProviderClient, TicketRepository
from src.usecases.exceptions import (
    EventNotFound,
    EventUnexpectedStatus,
    RegistrationDeadlinePassed,
    SeatNotAvailable,
    TicketNotFound,
)
from src.usecases.seats import GetSeatsUsecase, invalidate_seats_cache


class CreateTicketUsecase:
    """Зарегистрировать участника на событие.

    1. Найти событие в локальной БД.
    2. Проверить, что оно опубликовано.
    3. Проверить, что дедлайн не прошёл.
    4. Проверить, что место есть в списке свободных.
    5. Отправить запрос в Events Provider.
    6. Сохранить билет в локальной БД.
    7. Сбросить кэш мест.
    """

    def __init__(
        self,
        client: EventsProviderClient,
        events: EventRepository,
        tickets: TicketRepository,
        seats_usecase: GetSeatsUsecase,
    ) -> None:
        self._client = client
        self._events = events
        self._tickets = tickets
        self._seats_usecase = seats_usecase

    async def do(
        self,
        event_id: str,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> str:
        # 1. Найти событие
        event = await self._events.get(event_id)
        if event is None:
            raise EventNotFound

        # 2. Проверить статус
        if event.status.value != "published":
            raise EventUnexpectedStatus(event.status.value)

        # 3. Проверить дедлайн
        now = datetime.now(UTC)
        if now >= event.registration_deadline:
            raise RegistrationDeadlinePassed

        # 4. Проверить, что место свободно
        available_seats = await self._seats_usecase.do(event_id)
        if available_seats is not None and seat not in available_seats:
            raise SeatNotAvailable(seat)

        # 5. Регистрация в провайдере
        ticket_id = await self._client.register(
            event.id, first_name, last_name, email, seat
        )

        # 6. Сохранить билет локально
        await self._tickets.create(
            event.id, ticket_id, first_name, last_name, email, seat
        )

        # 7. Сбросить кэш мест
        invalidate_seats_cache(event_id)

        return ticket_id


class CancelTicketUsecase:
    """Отменить регистрацию — освободить место."""

    def __init__(
        self,
        client: EventsProviderClient,
        tickets: TicketRepository,
    ) -> None:
        self._client = client
        self._tickets = tickets

    async def do(self, ticket_id: str) -> bool:
        # 1. Найти билет в локальной БД
        ticket = await self._tickets.get(ticket_id)
        if ticket is None:
            raise TicketNotFound

        # 2. Отмена в провайдере
        result = await self._client.unregister(ticket.event_id, ticket_id)

        # 3. Удалить из локальной БД
        await self._tickets.delete(ticket_id)

        # 4. Сбросить кэш мест
        invalidate_seats_cache(ticket.event_id)

        return result
