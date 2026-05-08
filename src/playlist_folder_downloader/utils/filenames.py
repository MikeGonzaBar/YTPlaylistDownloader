"""Cross-platform filename helpers."""

from __future__ import annotations

import re

WINDOWS_RESERVED_CHARS = '<>:"/\\|?*'
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}
CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")
WHITESPACE_RE = re.compile(r"\s+")


def _fallback_for_name(name: str) -> str:
    lowered = name.lower()
    if "playlist" in lowered:
        return "Untitled Playlist"
    return "Untitled Video"


def sanitize_filename(name: str, max_length: int = 150) -> str:
    """Sanitize a filename component for Windows, macOS, and Linux."""

    fallback = _fallback_for_name(name)
    value = CONTROL_CHARS_RE.sub("", name or "")
    value = "".join("_" if char in WINDOWS_RESERVED_CHARS else char for char in value)
    value = WHITESPACE_RE.sub(" ", value).strip(" .")

    if not value:
        value = fallback

    if len(value) > max_length:
        value = value[:max_length].rstrip(" .")

    if not value:
        value = fallback

    stem = value.split(".", 1)[0].upper()
    if stem in WINDOWS_RESERVED_NAMES:
        value = f"_{value}"

    return value


def make_playlist_folder_name(title: str, playlist_id: str) -> str:
    """Return a safe folder name for a playlist."""

    base_title = title.strip() if title and title.strip() else "Untitled Playlist"
    return sanitize_filename(base_title, max_length=150)


def make_video_prefix(index: int | None) -> str:
    """Return a sortable playlist index prefix."""

    if index is None or index < 1:
        return "000"
    return f"{index:03d}"
