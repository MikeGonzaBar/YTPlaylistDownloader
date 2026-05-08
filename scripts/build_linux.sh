#!/usr/bin/env bash
set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install uv first, then rerun this script." >&2
  exit 1
fi

uv sync --extra dev
uv run python scripts/check_env.py
uv run python -m pytest -q
uv run python -m ruff check .

uv run python -m PyInstaller \
  --name "Playlist Folder Downloader" \
  --windowed \
  --clean \
  --add-data "src/playlist_folder_downloader/i18n:playlist_folder_downloader/i18n" \
  --add-data "README.md:." \
  --add-data "LICENSE:." \
  "src/playlist_folder_downloader/__main__.py"
