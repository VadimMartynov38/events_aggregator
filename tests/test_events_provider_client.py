"""Тесты EventsProviderClient с unittest.mock.

Мокаем httpx.AsyncClient, чтобы не делать реальных HTTP-запросов.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.clients.events_provider import EventsProviderClient, SeatAlreadyTaken, _parse_event
from src.domain import Event, EventStatus


@pytest.fixture
def client():
    return EventsProviderClient(
        base_url="http://test-provider.example",
        api_key="test-key",
        timeout=5.0,
    )


def _mock_response(status_code: int, json_data: dict | list | None = None) -> MagicMock:
    """Создать mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}

    if status_code >= 400:
        error = httpx.HTTPStatusError("error", request=MagicMock(), response=resp)
        resp.raise_for_status.side_effect = error
    else:
        resp.raise_for_status = MagicMock()

    return resp


class TestEventsMethod:
    """Тесты метода events()."""

    async def test_events_returns_page(self, client, sample_event_raw):
        """events() возвращает сырой JSON со страницей."""
        mock_resp = _mock_response(
            200,
            {
                "next": None,
                "previous": None,
                "results": [sample_event_raw],
            },
        )

        mock_http = MagicMock()
        mock_http.get = AsyncMock(return_value=mock_resp)
        with patch.object(client, "_ensure_client", return_value=mock_http):
            result = await client.events(changed_at="2000-01-01")

        assert result["next"] is None
        assert len(result["results"]) == 1
        assert result["results"][0]["id"] == sample_event_raw["id"]

    async def test_events_with_cursor(self, client, sample_event_raw):
        """events() передаёт cursor в параметрах."""
        mock_resp = _mock_response(
            200,
            {
                "next": None,
                "previous": "http://prev",
                "results": [sample_event_raw],
            },
        )

        mock_get = AsyncMock(return_value=mock_resp)
        mock_http = MagicMock()
        mock_http.get = mock_get
        with patch.object(client, "_ensure_client", return_value=mock_http):
            await client.events(changed_at="2026-01-01", cursor="abc123")

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args.kwargs["params"]["changed_at"] == "2026-01-01"
        assert call_args.kwargs["params"]["cursor"] == "abc123"

    async def test_events_raises_on_error(self, client):
        """events() поднимает исключение при HTTP-ошибке."""
        mock_resp = _mock_response(401, {"detail": "Unauthorized"})

        mock_http = MagicMock()
        mock_http.get = AsyncMock(return_value=mock_resp)
        with patch.object(client, "_ensure_client", return_value=mock_http):
            with pytest.raises(httpx.HTTPStatusError):
                await client.events(changed_at="2000-01-01")


class TestFetchSeatsMethod:
    """Тесты метода fetch_seats()."""

    async def test_fetch_seats_returns_list(self, client):
        """fetch_seats() возвращает список строк."""
        mock_resp = _mock_response(200, {"seats": ["A1", "A3", "B2"]})

        mock_http = MagicMock()
        mock_http.get = AsyncMock(return_value=mock_resp)
        with patch.object(client, "_ensure_client", return_value=mock_http):
            seats = await client.fetch_seats("event-1")

        assert seats == ["A1", "A3", "B2"]

    async def test_fetch_seats_returns_none_on_404(self, client):
        """fetch_seats() возвращает None при 404."""
        mock_resp = _mock_response(404)

        mock_http = MagicMock()
        mock_http.get = AsyncMock(return_value=mock_resp)
        with patch.object(client, "_ensure_client", return_value=mock_http):
            seats = await client.fetch_seats("nonexistent")

        assert seats is None


class TestRegisterMethod:
    """Тесты метода register()."""

    async def test_register_returns_ticket_id(self, client):
        """register() возвращает ticket_id из ответа."""
        mock_resp = _mock_response(201, {"ticket_id": "ticket-123"})

        mock_post = AsyncMock(return_value=mock_resp)
        mock_http = MagicMock()
        mock_http.post = mock_post
        with patch.object(client, "_ensure_client", return_value=mock_http):
            ticket_id = await client.register(
                event_id="event-1",
                first_name="Иван",
                last_name="Иванов",
                email="ivan@example.com",
                seat="A1",
            )

        assert ticket_id == "ticket-123"
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "/api/events/event-1/register/" in call_args.args[0]
        assert call_args.kwargs["json"]["first_name"] == "Иван"
        assert call_args.kwargs["json"]["email"] == "ivan@example.com"
        assert call_args.kwargs["json"]["seat"] == "A1"

    async def test_register_raises_on_400(self, client):
        """register() поднимает SeatAlreadyTaken при 400."""
        mock_resp = _mock_response(400, {"detail": "Seat taken"})

        mock_http = MagicMock()
        mock_http.post = AsyncMock(return_value=mock_resp)
        with patch.object(client, "_ensure_client", return_value=mock_http):
            with pytest.raises(SeatAlreadyTaken):
                await client.register("event-1", "Иван", "Иванов", "ivan@example.com", "A1")


class TestUnregisterMethod:
    """Тесты метода unregister()."""

    async def test_unregister_returns_true(self, client):
        """unregister() отправляет DELETE и возвращает True."""
        mock_resp = _mock_response(200, {"success": True})

        mock_request = AsyncMock(return_value=mock_resp)  # ← переименовали
        mock_http = MagicMock()
        mock_http.request = mock_request  # ← request вместо delete
        with patch.object(client, "_ensure_client", return_value=mock_http):
            result = await client.unregister("event-1", "ticket-123")

        assert result is True
        mock_request.assert_called_once_with(
            "DELETE",
            "/api/events/event-1/unregister/",
            json={"ticket_id": "ticket-123"},
        )


class TestParseEvent:
    """Тесты функции _parse_event."""

    def test_parse_event_creates_domain_event(self, sample_event_raw):
        """_parse_event корректно создаёт доменный Event."""
        event = _parse_event(sample_event_raw)
        assert event.id == sample_event_raw["id"]
        assert event.place.city == "Москва"
        assert event.place.seats_pattern == "A1-1000,B1-2000"
        assert event.status == EventStatus.published
        assert isinstance(event, Event)

    def test_parse_event_handles_missing_visitors(self, sample_event_raw):
        """_parse_event ставит 0 при отсутствии number_of_visitors."""
        raw = {**sample_event_raw}
        del raw["number_of_visitors"]
        event = _parse_event(raw)
        assert event.number_of_visitors == 0
