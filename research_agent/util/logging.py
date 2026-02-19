"""Structured logging setup."""

from __future__ import annotations

import logging
import sys

from research_agent.config import settings


def setup_logging(run_id: str | None = None) -> logging.Logger:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    fmt = "%(asctime)s %(levelname)-8s [%(name)s]"
    if run_id:
        fmt += f" [run={run_id}]"
    fmt += " %(message)s"

    logging.basicConfig(format=fmt, level=level, stream=sys.stderr, force=True)
    logger = logging.getLogger("research_agent")
    logger.setLevel(level)
    return logger
