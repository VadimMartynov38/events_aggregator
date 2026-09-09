"""Доменные исключения бизнес-логики."""


class EventNotFound(Exception):  # noqa: N818
    """Событие не найдено в локальной БД."""


class EventUnexpectedStatus(Exception):  # noqa: N818
    """Событие не опубликовано — регистрация недоступна."""

    def __init__(self, status: str) -> None:
        self.status = status
        super().__init__(f"Событие не опубликовано (статус: {status})")


class SeatAlreadyTaken(Exception):  # noqa: N818
    """Место уже занято."""


class SeatNotAvailable(Exception):  # noqa: N818
    """Место не в списке свободных."""

    def __init__(self, seat: str) -> None:
        self.seat = seat
        super().__init__(f"Место {seat} недоступно")


class RegistrationDeadlinePassed(Exception):  # noqa: N818
    """Дедлайн регистрации прошёл."""


class TicketNotFound(Exception):  # noqa: N818
    """Билет не найден."""
