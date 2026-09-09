"""Тесты EventsPaginator — асинхронного итератора.

Мокаем EventsProviderClient.events() — реальных запросов нет.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

from src.clients.paginator import EventsPaginator


def _make_page(
    results: list[dict],
    next_url: str | None = None,
    previous_url: str | None = None,
) -> dict:
    return {
        "next": next_url,
        "previous": previous_url,
        "results": results,
    }


class TestEventsPaginatorSinglePage:
    """Пагинация: одна страница."""

    async def test_single_page(self, sample_event_raw):
        """Одна страница — отдаёт все события, потом StopAsyncIteration."""
        mock_client = AsyncMock()
        mock_client.events = AsyncMock(return_value=_make_page([sample_event_raw], next_url=None))

        paginator = EventsPaginator(mock_client, changed_at="2000-01-01")

        collected = []
        async for event in paginator:
            collected.append(event)

        assert len(collected) == 1
        assert collected[0].id == sample_event_raw["id"]
        assert paginator.total_yielded == 1
        mock_client.events.assert_called_once()

    async def test_empty_page(self):
        """Пустая страница — сразу StopAsyncIteration."""
        mock_client = AsyncMock()
        mock_client.events = AsyncMock(return_value=_make_page([], next_url=None))

        paginator = EventsPaginator(mock_client, changed_at="2000-01-01")

        collected = []
        async for event in paginator:
            collected.append(event)

        assert collected == []
        assert paginator.total_yielded == 0


class TestEventsPaginatorMultiplePages:
    """Пагинация: несколько страниц."""

    async def test_multiple_pages(self, sample_event_raw, sample_event_raw_2):
        """Две страницы — отдаёт события из обеих."""
        page1 = _make_page(
            [sample_event_raw],
            next_url=("http://provider/api/events/?changed_at=2000-01-01&cursor=abc"),
        )
        page2 = _make_page([sample_event_raw_2], next_url=None)

        mock_client = AsyncMock()
        mock_client.events = AsyncMock(side_effect=[page1, page2])

        paginator = EventsPaginator(mock_client, changed_at="2000-01-01")

        collected = []
        async for event in paginator:
            collected.append(event)

        assert len(collected) == 2
        assert collected[0].id == sample_event_raw["id"]
        assert collected[1].id == sample_event_raw_2["id"]
        assert paginator.total_yielded == 2
        assert mock_client.events.call_count == 2

    async def test_cursor_passed_between_pages(self, sample_event_raw, sample_event_raw_2):
        """Курсор из next_url передаётся в следующий запрос."""
        page1 = _make_page(
            [sample_event_raw],
            next_url=("http://provider/api/events/?changed_at=2000-01-01&cursor=next-cursor-xyz"),
        )
        page2 = _make_page([sample_event_raw_2], next_url=None)

        mock_client = AsyncMock()
        mock_client.events = AsyncMock(side_effect=[page1, page2])

        paginator = EventsPaginator(mock_client, changed_at="2000-01-01")

        collected = []
        async for event in paginator:
            collected.append(event)

        assert len(collected) == 2

        # Первый вызов — без cursor
        first_call = mock_client.events.call_args_list[0]
        assert first_call.kwargs["changed_at"] == "2000-01-01"
        assert first_call.kwargs["cursor"] is None

        # Второй вызов — с cursor из next_url
        second_call = mock_client.events.call_args_list[1]
        assert second_call.kwargs["changed_at"] == "2000-01-01"
        assert second_call.kwargs["cursor"] == "next-cursor-xyz"


class TestEventsPaginatorLargeBatch:
    """Пагинация: несколько событий на странице."""

    async def test_multiple_events_per_page(self):
        """Несколько событий на одной странице."""
        raw_events = [
            {
                "id": f"event-{i}",
                "name": f"Событие {i}",
                "place": {
                    "id": f"place-{i}",
                    "name": f"Площадка {i}",
                    "city": "Москва",
                    "address": f"Адрес {i}",
                    "seats_pattern": "A1-10",
                    "changed_at": "2025-01-01T03:00:00+03:00",
                    "created_at": "2025-01-01T03:00:00+03:00",
                },
                "event_time": "2026-01-11T17:00:00+03:00",
                "registration_deadline": "2026-01-10T17:00:00+03:00",
                "status": "published",
                "number_of_visitors": 0,
                "changed_at": "2026-01-04T22:28:35+03:00",
                "created_at": "2026-01-04T22:28:35+03:00",
                "status_changed_at": "2026-01-04T22:28:35+03:00",
            }
            for i in range(5)
        ]

        mock_client = AsyncMock()
        mock_client.events = AsyncMock(return_value=_make_page(raw_events, next_url=None))

        paginator = EventsPaginator(mock_client, changed_at="2000-01-01")

        collected = []
        async for event in paginator:
            collected.append(event)

        assert len(collected) == 5
        assert paginator.total_yielded == 5
        mock_client.events.assert_called_once()


class TestEventsPaginatorChangedAt:
    """Проверка передачи changed_at."""

    async def test_changed_at_passed_to_client(self, sample_event_raw):
        """changed_at передаётся в клиент корректно."""
        mock_client = AsyncMock()
        mock_client.events = AsyncMock(return_value=_make_page([sample_event_raw], next_url=None))

        paginator = EventsPaginator(mock_client, changed_at="2026-06-01")
        async for _ in paginator:
            pass

        call_args = mock_client.events.call_args
        assert call_args.kwargs["changed_at"] == "2026-06-01"
