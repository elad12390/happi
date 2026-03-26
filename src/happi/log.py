from __future__ import annotations

import logging

from rich.console import Console
from rich.logging import RichHandler

_logger = logging.getLogger("happi")
_configured = False


def get_logger(name: str | None = None) -> logging.Logger:
    if name:
        return logging.getLogger(f"happi.{name}")
    return _logger


def configure_logging(*, verbose: bool = False, debug: bool = False) -> None:
    global _configured
    if _configured:
        return
    _configured = True

    level = logging.WARNING
    if verbose:
        level = logging.INFO
    if debug:
        level = logging.DEBUG

    handler = RichHandler(
        level=level,
        console=Console(stderr=True),
        show_time=debug,
        show_path=debug,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=debug,
    )

    _logger.setLevel(level)
    _logger.addHandler(handler)
    _logger.propagate = False
