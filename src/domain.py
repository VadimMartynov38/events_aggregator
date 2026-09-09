"""Доменные модели — ядро бизнес-логики, не зависит от фреймворков и БД."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class EventStatus(str, Enum):
    new = "new"
    published = "published"
    finished = "finished"
    cancelled = "cancelled"


@dataclass(frozen=True)
class Place:
    id: str
    name: str
    city: str
    address: str
    seats_pattern: str
    changed_at: datetime
    created_at: datetime


@dataclass(frozen=True)
class Event:
    id: str
    name: str
    place: Place
    event_time: datetime
    registration_deadline: datetime
    status: EventStatus
    number_of_visitors: int
    changed_at: datetime
    created_at: datetime
    status_changed_at: datetime


@dataclass(frozen=True)
class Ticket:
    id: str
    event_id: str
    first_name: str
    last_name: str
    email: str
    seat: str
    created_at: datetime


@dataclass(frozen=True)
class SyncMeta:
    id: int
    last_sync_time: datetime | None
    last_changed_at: datetime | None
    sync_status: str
    events_synced: int
    error_message: str | None
