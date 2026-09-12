"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db import get_session
from src.deps import get_sync_meta_repo
from src.schemas import HealthSchema

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthSchema)
async def health(session: AsyncSession = Depends(get_session)):
    """Проверка доступности сервиса и статуса последней синхронизации."""
    sync_repo = get_sync_meta_repo(session)
    meta = await sync_repo.get()

    return HealthSchema(
        status="ok",
        provider_url=settings.provider_base_url,
        last_sync=meta.last_sync_time if meta else None,
        sync_status=meta.sync_status if meta else None,
    )
