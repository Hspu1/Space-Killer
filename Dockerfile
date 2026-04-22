ARG BASE_IMAGE=ghcr.io/astral-sh/uv:python3.12-bookworm-slim

FROM $BASE_IMAGE AS builder
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

FROM $BASE_IMAGE AS runtime
ARG APP_PORT=8000
WORKDIR /app

RUN useradd -u 1000 app && mkdir -p /app && chown app:app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONOPTIMIZE=1 \
    HOME=/app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app ./src ./src
COPY --chown=app:app ./templates ./templates
COPY --chown=app:app ./frontend ./frontend
COPY --chown=app:app ./alembic.ini ./

USER app

CMD ["sh", "-c", "exec granian --interface asgi src.main:app \
    --host 0.0.0.0 \
    --port ${APP_PORT} \
    --loop uvloop \
    --http 1 \
    --workers 2"]


EXPOSE ${APP_PORT}
