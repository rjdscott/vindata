# Multi-stage Dockerfile for the API. The final image runs both Alembic
# (for migrations on container start) and uvicorn (the app).
# Build context is the repo root; we COPY only what we need.

# ----- builder: install deps with uv into a virtualenv we copy across -----
FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_NO_CACHE=1

# uv binary
COPY --from=ghcr.io/astral-sh/uv:0.5.13 /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy only what affects dep resolution first for layer caching.
COPY pyproject.toml /app/
COPY apps/api/pyproject.toml /app/apps/api/
COPY apps/ingest/pyproject.toml /app/apps/ingest/
COPY packages/agronomy/pyproject.toml /app/packages/agronomy/

# Then sources.
COPY apps/api /app/apps/api
COPY packages/agronomy /app/packages/agronomy

RUN uv venv /opt/venv \
 && uv pip install --python /opt/venv/bin/python \
      -e /app/packages/agronomy \
      -e /app/apps/api

# ----- runtime -----
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}"

# libpq for psycopg's binary build (transitive runtime dep on libssl/libpq).
RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

# Drop privileges.
RUN useradd --system --uid 1000 --home /app vindata \
 && chown -R vindata:vindata /app
USER vindata

EXPOSE 8000
CMD ["uvicorn", "vindata_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
