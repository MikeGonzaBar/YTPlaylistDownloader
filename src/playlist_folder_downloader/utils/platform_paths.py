"""Platform path helpers."""

from __future__ import annotations

from pathlib import Path

from platformdirs import user_config_path, user_downloads_path

from playlist_folder_downloader.constants import APP_AUTHOR, APP_ID


def app_config_dir() -> Path:
    return user_config_path(APP_ID, APP_AUTHOR, ensure_exists=True)


def settings_file_path() -> Path:
    return app_config_dir() / "settings.json"


def default_download_root() -> Path:
    try:
        return user_downloads_path()
    except Exception:
        return Path.home() / "Downloads"
