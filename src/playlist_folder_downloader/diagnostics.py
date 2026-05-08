"""Lightweight terminal diagnostics for long-running GUI work."""

from __future__ import annotations

import re
import sys
from datetime import datetime

QUERY_RE = re.compile(r"(https?://\S+?)\?\S+")


def debug_print(message: str) -> None:
    """Print a timestamped diagnostic line immediately.

    These messages intentionally avoid signed media URLs, cookies, credentials,
    and secrets. They are for local troubleshooting when yt-dlp or Qt work takes
    longer than expected.
    """

    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] Playlist Folder Downloader: {message}", file=sys.stderr, flush=True)


def redact_urls(message: str) -> str:
    """Redact URL query strings before writing third-party diagnostics."""

    return QUERY_RE.sub(r"\1?[redacted]", message)


class YtDlpDiagnosticLogger:
    """yt-dlp logger that prints warning/error diagnostics without full URLs."""

    def debug(self, message: str) -> None:
        if message.startswith("[debug]"):
            return
        debug_print(f"yt-dlp: {redact_urls(message)}")

    def info(self, message: str) -> None:
        debug_print(f"yt-dlp: {redact_urls(message)}")

    def warning(self, message: str) -> None:
        debug_print(f"yt-dlp warning: {redact_urls(message)}")

    def error(self, message: str) -> None:
        debug_print(f"yt-dlp error: {redact_urls(message)}")
