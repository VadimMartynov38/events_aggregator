"""Pydantic-схемы для API-запросов и ответов."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class PlaceSchema(BaseModel):
    id: str
    name: str
    city: str
    address: str


class PlaceDetailSchema(PlaceSchema):
    seats_pattern: str


class EventSchema(BaseModel):
    id: str
    name: str
    place: PlaceSchema
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int


class EventDetailSchema(EventSchema):
    place: PlaceDetailSchema


class PaginatedEventsSchema(BaseModel):
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    results: list[EventSchema]


class SeatsSchema(BaseModel):
    event_id: str
    available_seats: list[str]


class RegisterRequestSchema(BaseModel):
    event_id: str
    first_name: str = Field(..., min_length=1, max_length=200)
    last_name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    seat: str = Field(..., min_length=1, max_length=20)


class RegisterResponseSchema(BaseModel):
    ticket_id: str


class CancelResponseSchema(BaseModel):
    success: bool


class HealthSchema(BaseModel):
    status: str
    provider_url: str
    last_sync: Optional[datetime] = None
    sync_status: Optional[str] = None


class SyncTriggerResponseSchema(BaseModel):
    status: str
    events_synced: int