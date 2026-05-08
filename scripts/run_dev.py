"""Run Playlist Folder Downloader from a source checkout."""

from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))


if __name__ == "__main__":
    main = import_module("playlist_folder_downloader.__main__").main
    raise SystemExit(main())
