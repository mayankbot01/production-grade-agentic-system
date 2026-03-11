FROM python:3.13.2-slim

WORKDIR /app

ARG APP_ENV=production
ENV APP_ENV=${APP_ENV} \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && pip install --upgrade pip \
    && pip install uv \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN uv venv && . .venv/bin/activate && uv pip install -e .

COPY . .

RUN chmod +x /app/scripts/docker-entrypoint.sh

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

RUN mkdir -p /app/logs

EXPOSE 8000

ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
CMD ["/app/.venv/bin/uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
