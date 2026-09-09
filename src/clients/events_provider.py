"""HTTP-клиент для Events Provider API.

Единственный класс, который общается со сторонним сервисом.
Отвечает за HTTP-запросы и преобразование JSON -> доменные модели.
"""

from __future__ import annotations

import logging
from datetime import datetime

import httpx

from src.config import settings
from src.domain import Event, EventStatus, Place

logger = logging.getLogger(__name__)


class SeatAlreadyTaken(Exception):
    """Место уже занято."""


class RegistrationClosed(Exception):
    """Регистрация недоступна — событие не опубликовано или дедлайн прошёл."""


class EventsProviderClient:
    """Асинхронный клиент Events Provider API."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self._base_url = (base_url or settings.provider_base_url).rstrip("/")
        self._api_key = api_key or settings.provider_api_key
        self._timeout = timeout or settings.request_timeout
        self._client: httpx.AsyncClient | None = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers={"x-api-key": self._api_key},
                timeout=self._timeout,
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ── Events ─────────────────────────────────────────────────

    async def events(
        self, changed_at: str, cursor: str | None = None
    ) -> dict:
        """Получить одну страницу событий.

        Returns:
            Сырой JSON: {"next": ..., "previous": ..., "results": [...]}
        """
        client = await self._ensure_client()
        params: dict = {"changed_at": changed_at}
        if cursor:
            params["cursor"] = cursor

        resp = await client.get("/api/events/", params=params)
        resp.raise_for_status()
        return resp.json()

    # ── Seats ───────────────────────────────────────────────────

    async def fetch_seats(self, event_id: str) -> list[str] | None:
        """Получить список свободных мест для события.

        Returns:
            Список ID мест (например ["A1", "A3"]) или None, если событие не найдено.
        """
        client = await self._ensure_client()
        resp = await client.get(f"/api/events/{event_id}/seats/")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        return data.get("seats", [])

    # ── Registration ────────────────────────────────────────────

    async def register(
        self,
        event_id: str,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> str:
        """Зарегистрировать участника. Возвращает ticket_id."""
        client = await self._ensure_client()
        resp = await client.post(
            f"/api/events/{event_id}/register/",
            json={
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "seat": seat,
            },
        )
        if resp.status_code == 400:
            raise SeatAlreadyTaken(
                f"Место {seat} уже занято или некорректные данные"
            )
        if resp.status_code == 404:
            raise EventNotFoundExternal(f"Событие {event_id} не найдено")
        resp.raise_for_status()
        data = resp.json()
        return data.get("ticket_id", data.get("id", ""))

    async def unregister(self, event_id: str, ticket_id: str) -> bool:
        """Отменить регистрацию по ticket_id."""
        client = await self._ensure_client()
        resp = await client.request(
            "DELETE",
            f"/api/events/{event_id}/unregister/",
            json={"ticket_id": ticket_id},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("success", True)


class EventNotFoundExternal(Exception):
    """Событие не найдено во внешнем API."""


# ── Парсинг ───────────────────────────────────────────────────

def _parse_event(raw: dict) -> Event:
    place_raw = raw.get("place", {})
    status_raw = raw.get("status", "new")
    try:
        status = EventStatus(status_raw)
    except ValueError:
        status = EventStatus.new
    return Event(
        id=raw["id"],
        name=raw["name"],
        place=Place(
            id=place_raw["id"],
            name=place_raw["name"],
            city=place_raw["city"],
            address=place_raw["address"],
            seats_pattern=place_raw["seats_pattern"],
            changed_at=datetime.fromisoformat(place_raw["changed_at"]),
            created_at=datetime.fromisoformat(place_raw["created_at"]),
        ),
        event_time=datetime.fromisoformat(raw["event_time"]),
        registration_deadline=datetime.fromisoformat(
            raw["registration_deadline"]
        ),
        status=status,
        number_of_visitors=raw.get("number_of_visitors", 0),
        changed_at=datetime.fromisoformat(raw["changed_at"]),
        created_at=datetime.fromisoformat(raw["created_at"]),
        status_changed_at=datetime.fromisoformat(raw["status_changed_at"]),
    )
