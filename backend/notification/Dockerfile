FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/
COPY db/ ./db/
COPY alembic/ ./alembic/
COPY alembic.ini .

RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser


CMD ["sh", "-c", "alembic upgrade head && exec python -m app.worker"]
