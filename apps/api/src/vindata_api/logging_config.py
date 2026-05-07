"""Structured JSON logging via ``structlog``.

Bound to stdlib ``logging`` so SQLAlchemy / uvicorn / FastAPI logs flow
through the same JSON pipeline. Console-friendly tracebacks in dev (TTY),
strict JSON in containers (non-TTY).
"""

from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(level: str = "info") -> None:
    """Idempotent. Safe to call multiple times in tests."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
        force=True,
    )

    is_tty = sys.stdout.isatty()
    renderer: structlog.types.Processor = (
        structlog.dev.ConsoleRenderer(colors=True)
        if is_tty
        else structlog.processors.JSONRenderer()
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )
