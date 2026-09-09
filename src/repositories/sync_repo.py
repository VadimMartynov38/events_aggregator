"""SQLAlchemy-реализация SyncMetaRepository."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.db import SyncMetaRow
from src.domain import SyncMeta


class SqlSyncMetaRepository:
    """Репозиторий метаданных синхронизации (одна строка, id=1)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self) -> SyncMeta | None:
        row = await self._session.get(SyncMetaRow, 1)
        if row is None:
            return None
        return SyncMeta(
            id=row.id,
            last_sync_time=row.last_sync_time,
            last_changed_at=row.last_changed_at,
            sync_status=row.sync_status,
            events_synced=row.events_synced,
            error_message=row.error_message,
        )

    async def update(
        self,
        last_sync_time: datetime,
        last_changed_at: datetime | None,
        sync_status: str,
        events_synced: int,
        error_message: str | None = None,
    ) -> None:
        row = await self._session.get(SyncMetaRow, 1)
        if row is None:
            row = SyncMetaRow(
                id=1,
                last_sync_time=last_sync_time,
                last_changed_at=last_changed_at,
                sync_status=sync_status,
                events_synced=events_synced,
                error_message=error_message,
            )
            self._session.add(row)
        else:
            row.last_sync_time = last_sync_time
            row.last_changed_at = last_changed_at
            row.sync_status = sync_status
            row.events_synced = events_synced
            row.error_message = error_message
        await self._session.commit()