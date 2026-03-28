"""
Structured logging setup.

* **Development**: human-readable, coloured console output.
* **Production**: JSON-formatted logs for machine parsing.

Logs are emitted to both the console and a rotating log file under
``backend/logs/``.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

try:
    from pythonjsonlogger import jsonlogger  # type: ignore[import-untyped]
except ImportError:
    from pythonjsonlogger.json import JsonFormatter as _JF  # newer versions
    class _Compat:
        JsonFormatter = _JF
    jsonlogger = _Compat()

# ── Constants ───────────────────────────────────────────────────────────
_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
_LOG_FILE = _LOG_DIR / "app.log"
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB per file
_BACKUP_COUNT = 5
_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_JSON_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def _setup_logging() -> None:
    """Configure the root logger with console and file handlers."""
    # Ensure the log directory exists
    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers on repeated calls
    if root_logger.handlers:
        return

    # ── Console handler (human-readable) ────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(_LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # ── File handler (JSON for production, readable for dev) ────────
    file_handler = RotatingFileHandler(
        _LOG_FILE,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)

    json_formatter = jsonlogger.JsonFormatter(
        _JSON_FORMAT,
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    file_handler.setFormatter(json_formatter)
    root_logger.addHandler(file_handler)

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


# Initialise logging on import
_setup_logging()


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.

    Args:
        name: Usually ``__name__`` of the calling module.

    Returns:
        A ``logging.Logger`` configured with the project's handlers.
    """
    return logging.getLogger(name)
