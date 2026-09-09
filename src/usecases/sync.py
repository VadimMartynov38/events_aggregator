"""Use case фоновой синхронизации событий.

Использует EventsPaginator (итератор) для обхода страниц
и EventRepository для upsert в локальную БД.
Хранит метаданные через SyncMetaRepository.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from src.clients.events_provider import EventsProviderClient
from src.clients.paginator import EventsPaginator
from src.protocols import EventRepository, SyncMetaRepository

logger = logging.getLogger(__name__)


class SyncEventsUsecase:
    """Синхронизировать события из Events Provider в локальную БД.

    Шаги:
    1. Прочитать метаданные последней синхронизации.
    2. Вычислить changed_at (максимальный из БД или 2000-01-01).
    3. Пройти через EventsPaginator, сохранить все события батчами.
    4. Обновить метаданные.
    """

    def __init__(
        self,
        client: EventsProviderClient,
        events: EventRepository,
        sync_meta: SyncMetaRepository,
    ) -> None:
        self._client = client
        self._events = events
        self._sync_meta = sync_meta

    async def do(self) -> int:
        """Выполнить одну итерацию синхронизации.

        Returns:
            Количество синхронизированных событий.
        """
        # 1. Метаданные
        meta = await self._sync_meta.get()
        if meta and meta.last_changed_at:
            changed_at = meta.last_changed_at.date().isoformat()
        else:
            changed_at = "2000-01-01"

        logger.info("Синхронизация: changed_at=%s", changed_at)

        total_synced = 0
        max_changed_at: datetime | None = None

        try:
            # 2. Обход через пагинатор
            paginator = EventsPaginator(self._client, changed_at=changed_at)
            batch: list = []

            async for event in paginator:
                batch.append(event)
                if max_changed_at is None or event.changed_at > max_changed_at:
                    max_changed_at = event.changed_at

                # Сохраняем батчами по 50
                if len(batch) >= 50:
                    await self._events.upsert_many(batch)
                    total_synced += len(batch)
                    logger.info(
                        "Синхронизация: сохранено %d событий (всего %d)",
                        len(batch),
                        total_synced,
                    )
                    batch.clear()

            # Остаток
            if batch:
                await self._events.upsert_many(batch)
                total_synced += len(batch)

        except Exception as exc:
            logger.exception("Ошибка синхронизации: %s", exc)
            await self._sync_meta.update(
                last_sync_time=datetime.now(timezone.utc),
                last_changed_at=max_changed_at,
                sync_status="error",
                events_synced=total_synced,
                error_message=str(exc),
            )
            raise

        # 3. Метаданные
        await self._sync_meta.update(
            last_sync_time=datetime.now(timezone.utc),
            last_changed_at=max_changed_at,
            sync_status="success",
            events_synced=total_synced,
        )

        logger.info("Синхронизация завершена: %d событий", total_synced)
        return total_synced