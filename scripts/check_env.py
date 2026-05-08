"""Check local development/runtime dependencies."""

from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))


def main() -> int:
    check_dependencies = import_module(
        "playlist_folder_downloader.services.dependency_checker"
    ).check_dependencies
    print(f"Python: {sys.version.split()[0]}")
    status = check_dependencies()
    print(f"yt-dlp: {status.yt_dlp_version or 'missing'}")
    try:
        import PySide6  # noqa: F401
    except ImportError:
        print("PySide6: missing")
        pyside_available = False
    else:
        print("PySide6: available")
        pyside_available = True
    print(f"ffmpeg: {status.ffmpeg_path or 'missing'}")
    print(f"ffprobe: {status.ffprobe_path or 'missing'}")
    print(
        "JavaScript runtime: "
        f"{status.js_runtime_name or 'missing'}"
        f"{f' ({status.js_runtime_path})' if status.js_runtime_path else ''}"
    )
    for warning in status.warnings:
        print(f"Warning: {warning}")
    if not status.yt_dlp_available or not pyside_available:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
