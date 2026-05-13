ARG BASE_IMAGE=python:3.12-slim-bookworm
ARG APP_PORT=8000

FROM ${BASE_IMAGE} AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvbin/uv
ENV PATH="/uvbin:${PATH}"
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev --group app

FROM ${BASE_IMAGE} AS runtime
ARG APP_PORT
WORKDIR /app

RUN useradd -m -u 1000 app && mkdir -p /app && chown app:app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONOPTIMIZE=1 \
    HOME=/app
ENV APP_PORT=${APP_PORT}

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app ./src ./src
COPY --chown=app:app ./templates ./templates
COPY --chown=app:app deploy/alembic/alembic.ini deploy/alembic/alembic.ini

USER app

CMD ["sh", "-c", "exec granian --interface asgi src.main:app \
    --host 0.0.0.0 \
    --port ${APP_PORT} \
    --loop uvloop \
    --workers 1 \
    --http 1 \
    --opt"]
# N workers

EXPOSE ${APP_PORT}
