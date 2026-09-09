"""Точка входа — FastAPI с lifespan и фоновым воркером."""

from __future__ import annotations

import contextlib
import logging

from fastapi import FastAPI

from src.config import settings
from src.db import (  # init_db больше не нужен в lifespan
    async_session_factory, engine)
from src.deps import close_provider_client, get_provider_client
from src.repositories.event_repo import SqlEventRepository
from src.repositories.sync_repo import SqlSyncMetaRepository
from src.routers import events, health, seats, sync, tickets
from src.usecases.sync import SyncEventsUsecase
from src.worker.sync import SyncWorker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_sync_worker: SyncWorker | None = None


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл: воркер синхронизации -> shutdown.

    Миграции применяются через Alembic (run.sh),
    поэтому init_db() здесь не вызывается.
    """
    global _sync_worker

    logger.info("Запуск агрегатора событий")
    logger.info("Provider URL: %s", settings.provider_base_url)

    # init_db() убран — таблицы создаёт Alembic (alembic upgrade head в run.sh)

    # Воркер синхронизации
    client = get_provider_client()
    async with async_session_factory() as session:
        events_repo = SqlEventRepository(session)
        sync_meta_repo = SqlSyncMetaRepository(session)
        sync_usecase = SyncEventsUsecase(client, events_repo, sync_meta_repo)
        _sync_worker = SyncWorker(sync_usecase)
        await _sync_worker.start()

    yield

    logger.info("Остановка агрегатора...")
    if _sync_worker:
        await _sync_worker.stop()
    await close_provider_client()
    await engine.dispose()
    logger.info("Агрегатор остановлен")


app = FastAPI(
    title="Events Aggregator API",
    description=(
        "Промежуточный слой между клиентами и Events Provider API. "
        "Фоновая синхронизация, фильтрация, пагинация, регистрация."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(events.router)
app.include_router(seats.router)
app.include_router(tickets.router)
app.include_router(sync.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
