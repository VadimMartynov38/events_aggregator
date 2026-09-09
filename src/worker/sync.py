"""Воркер фоновой синхронизации на APScheduler.

Запускается в lifespan FastAPI и выполняет синхронизацию раз в N часов.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.config import settings
from src.usecases.sync import SyncEventsUsecase

logger = logging.getLogger(__name__)


class SyncWorker:
    """Воркер, периодически запускающий SyncEventsUsecase."""

    def __init__(
        self,
        sync_usecase: SyncEventsUsecase,
        interval_hours: int | None = None,
    ) -> None:
        self._sync_usecase = sync_usecase
        self._interval_hours = interval_hours or settings.sync_interval_hours
        self._scheduler: AsyncIOScheduler | None = None
        self._running = False

    async def _run_sync(self) -> None:
        """Обёртка для запуска usecase с обработкой ошибок."""
        if self._running:
            logger.warning("Синхронизация уже выполняется, пропускаем")
            return
        self._running = True
        try:
            await self._sync_usecase.do()
        except Exception:
            logger.exception("Ошибка в воркере синхронизации")
        finally:
            self._running = False

    async def start(self) -> None:
        """Запустить воркер: первичная синхронизация + расписание."""
        logger.info(
            "Воркер синхронизации запущен (интервал: %dч)", self._interval_hours
        )

        # Первичная синхронизация
        await self._run_sync()

        # Расписание
        self._scheduler = AsyncIOScheduler()
        self._scheduler.add_job(
            self._run_sync,
            IntervalTrigger(hours=self._interval_hours),
            id="sync_events",
            replace_existing=True,
        )
        self._scheduler.start()

    async def stop(self) -> None:
        """Остановить воркер."""
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
        logger.info("Воркер синхронизации остановлен")
