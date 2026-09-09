#!/bin/bash
set -e

# Создаём БД, если её нет (dev-окружение)
uv run python -c "
import asyncio
import asyncpg
from src.config import settings

async def ensure_db():
    url = settings.database_url.replace('+asyncpg', '')
    parts = url.split('/')
    db_name = parts[-1]
    server_url = '/'.join(parts[:-1]) + '/postgres'
    conn = await asyncpg.connect(server_url)
    exists = await conn.fetchval('SELECT 1 FROM pg_database WHERE datname = \$1', db_name)
    if not exists:
        await conn.execute(f'CREATE DATABASE {db_name}')
        print(f'БД {db_name} создана')
    await conn.close()

asyncio.run(ensure_db())
"

# Применяем миграции Alembic
uv run alembic upgrade head

# Запускаем API
uv run python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
