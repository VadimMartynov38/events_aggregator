"""Общие фикстуры для тестов."""

import pytest


@pytest.fixture
def sample_event_raw():
    """Сырой JSON события от провайдера."""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Конференция по Python",
        "place": {
            "id": "650e8400-e29b-41d4-a716-446655440001",
            "name": "Конференц-зал Технопарк",
            "city": "Москва",
            "address": "ул. Ленина, д. 1",
            "seats_pattern": "A1-1000,B1-2000",
            "changed_at": "2025-01-01T03:00:00+03:00",
            "created_at": "2025-01-01T03:00:00+03:00",
        },
        "event_time": "2026-01-11T17:00:00+03:00",
        "registration_deadline": "2026-01-10T17:00:00+03:00",
        "status": "published",
        "number_of_visitors": 5,
        "changed_at": "2026-01-04T22:28:35.325270+03:00",
        "created_at": "2026-01-04T22:28:35.325302+03:00",
        "status_changed_at": "2026-01-04T22:28:35.325386+03:00",
    }


@pytest.fixture
def sample_event_raw_2():
    """Второе событие для тестов пагинации."""
    return {
        "id": "660e8400-e29b-41d4-a716-446655440002",
        "name": "Митап по Go",
        "place": {
            "id": "760e8400-e29b-41d4-a716-446655440003",
            "name": "Хаб",
            "city": "Санкт-Петербург",
            "address": "Невский, д. 10",
            "seats_pattern": "A1-50",
            "changed_at": "2025-02-01T03:00:00+03:00",
            "created_at": "2025-02-01T03:00:00+03:00",
        },
        "event_time": "2026-02-15T18:00:00+03:00",
        "registration_deadline": "2026-02-14T18:00:00+03:00",
        "status": "new",
        "number_of_visitors": 0,
        "changed_at": "2026-01-05T10:00:00+03:00",
        "created_at": "2026-01-05T10:00:00+03:00",
        "status_changed_at": "2026-01-05T10:00:00+03:00",
    }
