"""Skupione funkcje konfiguracyjne loggera ElBotto."""

from __future__ import annotations

import logging
from typing import Optional


def setup_logging(level: str = "INFO", *, force: bool = False) -> None:
    """Inicjuje podstawową konfigurację logowania."""

    logger = logging.getLogger("elbotto")
    if force or not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Zwraca logger z przestrzeni nazw ElBotto."""

    base_name = "elbotto" if not name else f"elbotto.{name}"
    return logging.getLogger(base_name)
