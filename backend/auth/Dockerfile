FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Copy requirements first: this layer is cached until requirements change.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/
COPY db/ ./db/
COPY alembic/ ./alembic/
COPY alembic.ini .

RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
