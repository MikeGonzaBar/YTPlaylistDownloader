$ErrorActionPreference = "Stop"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
  throw "uv is required. Install uv first, then rerun this script."
}

uv sync --extra dev
uv run python scripts/check_env.py
uv run python -m pytest -q
uv run python -m ruff check .

uv run python -m PyInstaller `
  --name "Playlist Folder Downloader" `
  --windowed `
  --clean `
  --add-data "src/playlist_folder_downloader/i18n;playlist_folder_downloader/i18n" `
  --add-data "README.md;." `
  --add-data "LICENSE;." `
  "src/playlist_folder_downloader/__main__.py"
