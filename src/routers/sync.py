"""Роутер ручного запуска синхронизации."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.deps import get_events_repo, get_provider_client, get_sync_meta_repo
from src.schemas import SyncTriggerResponseSchema
from src.usecases.sync import SyncEventsUsecase

router = APIRouter(tags=["sync"])


@router.post("/api/sync/trigger/", response_model=SyncTriggerResponseSchema)
async def trigger_sync(
    session: AsyncSession = Depends(get_session),
):
    """Запустить синхронизацию вручную.

    Выполняется синхронно — клиент ждёт завершения.
    """
    client = get_provider_client()
    events_repo = get_events_repo(session)
    sync_meta_repo = get_sync_meta_repo(session)
    usecase = SyncEventsUsecase(client, events_repo, sync_meta_repo)

    try:
        count = await usecase.do()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return SyncTriggerResponseSchema(status="ok", events_synced=count)