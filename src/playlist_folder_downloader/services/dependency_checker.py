"""Runtime dependency detection."""

from __future__ import annotations

import importlib
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from playlist_folder_downloader.services.js_runtime import find_js_runtime


@dataclass(slots=True)
class DependencyStatus:
    yt_dlp_available: bool
    yt_dlp_version: str | None
    ffmpeg_available: bool
    ffmpeg_path: str | None
    ffprobe_available: bool
    ffprobe_path: str | None
    js_runtime_available: bool
    js_runtime_name: str | None
    js_runtime_path: str | None
    warnings: list[str] = field(default_factory=list)


def find_yt_dlp() -> tuple[bool, str | None]:
    """Return yt-dlp availability and version."""

    try:
        module = importlib.import_module("yt_dlp")
    except ImportError:
        return False, None
    return True, getattr(module, "version", None).__dict__.get("__version__") if hasattr(module, "version") else None


def _resolve_executable(name: str, configured_path: str | None = None) -> str | None:
    if configured_path:
        candidate = Path(configured_path).expanduser()
        if candidate.is_dir():
            binary = candidate / name
            if binary.exists():
                return str(binary)
        elif candidate.exists():
            return str(candidate)
    return shutil.which(name)


def find_ffmpeg(configured_path: str | None = None) -> str | None:
    return _resolve_executable("ffmpeg", configured_path)


def find_ffprobe(configured_path: str | None = None) -> str | None:
    return _resolve_executable("ffprobe", configured_path)


def check_dependencies(ffmpeg_path: str | None = None) -> DependencyStatus:
    yt_dlp_available, yt_dlp_version = find_yt_dlp()
    resolved_ffmpeg = find_ffmpeg(ffmpeg_path)
    resolved_ffprobe = find_ffprobe(ffmpeg_path)
    js_runtime_name, js_runtime_path = find_js_runtime()
    warnings: list[str] = []

    if not yt_dlp_available:
        warnings.append("yt-dlp is not installed. Playlist loading and downloads will not work.")
    if not resolved_ffmpeg:
        warnings.append("FFmpeg was not found. Merging, subtitles, and multi-audio downloads may fail.")
    if not resolved_ffprobe:
        warnings.append("ffprobe was not found. Some media inspection workflows may fail.")
    if not js_runtime_path:
        warnings.append("No JavaScript runtime was found. Some YouTube video formats may be unavailable.")

    return DependencyStatus(
        yt_dlp_available=yt_dlp_available,
        yt_dlp_version=yt_dlp_version,
        ffmpeg_available=resolved_ffmpeg is not None,
        ffmpeg_path=resolved_ffmpeg,
        ffprobe_available=resolved_ffprobe is not None,
        ffprobe_path=resolved_ffprobe,
        js_runtime_available=js_runtime_path is not None,
        js_runtime_name=js_runtime_name,
        js_runtime_path=js_runtime_path,
        warnings=warnings,
    )
