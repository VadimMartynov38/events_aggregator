FROM python:3.11-slim

WORKDIR /app

# Системные зависимости для asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY pyproject.toml ./
RUN uv sync --no-dev

COPY . .

RUN chmod +x run.sh

EXPOSE 8000

CMD ["bash", "./run.sh"]