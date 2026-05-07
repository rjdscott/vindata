"""FastAPI application factory.

Why a factory: tests can construct the app with overridden settings without
reaching into module-level state. Production uses ``app = create_app()`` at
import time so uvicorn can find it.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from vindata_api.db import init_db, shutdown_db
from vindata_api.logging_config import configure_logging
from vindata_api.routers import blocks, health, scores, vineyards
from vindata_api.settings import Settings, get_settings

log = structlog.get_logger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    init_db(settings)
    log.info("api.started", title=settings.title, version=settings.version)
    try:
        yield
    finally:
        await shutdown_db()
        log.info("api.stopped")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(level=settings.log_level)

    app = FastAPI(
        title=settings.title,
        version=settings.version,
        lifespan=_lifespan,
        docs_url="/docs",
        redoc_url=None,
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(vineyards.router)
    app.include_router(scores.router)
    app.include_router(blocks.router)
    return app


app = create_app()
