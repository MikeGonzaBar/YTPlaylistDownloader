"""JSON-backed user settings."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from playlist_folder_downloader.utils.platform_paths import (
    default_download_root,
    settings_file_path,
)


@dataclass(slots=True)
class AppSettings:
    download_root: str = field(default_factory=lambda: str(default_download_root()))
    language: str | None = None
    max_concurrent_downloads: int = 1
    ffmpeg_path: str | None = None
    default_quality: str = "Best"
    default_include_audio: bool = True
    default_include_video: bool = True
    default_subtitles_enabled: bool = False
    default_subtitle_languages: list[str] = field(default_factory=lambda: ["en"])


def _coerce_settings(data: dict[str, Any]) -> AppSettings:
    defaults = AppSettings()
    allowed = {
        "download_root",
        "language",
        "max_concurrent_downloads",
        "ffmpeg_path",
        "default_quality",
        "default_include_audio",
        "default_include_video",
        "default_subtitles_enabled",
        "default_subtitle_languages",
    }
    values = {key: data[key] for key in allowed if key in data}

    if not isinstance(values.get("download_root", defaults.download_root), str):
        values["download_root"] = defaults.download_root
    if values.get("language") is not None and not isinstance(values.get("language"), str):
        values["language"] = None
    if not isinstance(values.get("max_concurrent_downloads", defaults.max_concurrent_downloads), int):
        values["max_concurrent_downloads"] = defaults.max_concurrent_downloads
    values["max_concurrent_downloads"] = max(1, min(int(values.get("max_concurrent_downloads", 1)), 8))
    if values.get("ffmpeg_path") is not None and not isinstance(values.get("ffmpeg_path"), str):
        values["ffmpeg_path"] = None
    if not isinstance(values.get("default_quality", defaults.default_quality), str):
        values["default_quality"] = defaults.default_quality
    for key in ("default_include_audio", "default_include_video", "default_subtitles_enabled"):
        if not isinstance(values.get(key, getattr(defaults, key)), bool):
            values[key] = getattr(defaults, key)
    if not isinstance(values.get("default_subtitle_languages", defaults.default_subtitle_languages), list):
        values["default_subtitle_languages"] = defaults.default_subtitle_languages
    else:
        values["default_subtitle_languages"] = [
            str(item).strip()
            for item in values["default_subtitle_languages"]
            if str(item).strip()
        ] or ["en"]

    return AppSettings(**values)


def load_settings(path: str | Path | None = None) -> AppSettings:
    """Load settings from disk, falling back to defaults on missing/invalid data."""

    settings_path = Path(path) if path is not None else settings_file_path()
    if not settings_path.exists():
        return AppSettings()
    try:
        raw = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return AppSettings()
    if not isinstance(raw, dict):
        return AppSettings()
    return _coerce_settings(raw)


def save_settings(settings: AppSettings, path: str | Path | None = None) -> None:
    """Persist settings to disk as JSON."""

    settings_path = Path(path) if path is not None else settings_file_path()
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(asdict(settings), indent=2, sort_keys=True),
        encoding="utf-8",
    )
