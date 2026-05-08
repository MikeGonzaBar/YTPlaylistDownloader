"""Logging setup for the application."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from platformdirs import user_log_path

from playlist_folder_downloader.constants import APP_AUTHOR, APP_ID


def configure_logging() -> Path:
    """Configure console and rotating file logging.

    The app intentionally logs only high-level status and errors. It must not log
    signed media URLs, cookies, credentials, or other secrets.
    """

    log_dir = user_log_path(APP_ID, APP_AUTHOR, ensure_exists=True)
    log_path = log_dir / "app.log"

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    try:
        file_handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    except OSError:
        root.warning("Could not open log file at %s; continuing with console logging only.", log_path)
    else:
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    return log_path
