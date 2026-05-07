# Multi-stage Dockerfile for the Dagster code-location.
# Same uv-based pattern as apps/api.

FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_NO_CACHE=1

COPY --from=ghcr.io/astral-sh/uv:0.5.13 /uv /uvx /usr/local/bin/

WORKDIR /app

COPY pyproject.toml /app/
COPY apps/api/pyproject.toml /app/apps/api/
COPY apps/ingest/pyproject.toml /app/apps/ingest/
COPY packages/agronomy/pyproject.toml /app/packages/agronomy/

COPY apps/ingest /app/apps/ingest
COPY packages/agronomy /app/packages/agronomy

RUN uv venv /opt/venv \
 && uv pip install --python /opt/venv/bin/python \
      -e /app/packages/agronomy \
      -e /app/apps/ingest

FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}" \
    DAGSTER_HOME=/opt/dagster/dagster_home

RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 curl procps \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir -p /opt/dagster/dagster_home

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

# dagster.yaml is mounted from infra/local/dagster/dagster.yaml in compose.
# We do NOT bake it into the image so that config changes take effect
# without a Docker layer-cache rebuild.

RUN useradd --system --uid 1000 --home /app vindata \
 && chown -R vindata:vindata /app /opt/dagster
USER vindata

EXPOSE 3000
