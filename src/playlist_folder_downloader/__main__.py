"""Application entrypoint."""

from __future__ import annotations

import sys
from multiprocessing import freeze_support

from playlist_folder_downloader.app import create_app
from playlist_folder_downloader.diagnostics import debug_print


def main() -> int:
    freeze_support()
    app, window = create_app(sys.argv)
    window.show()
    debug_print("main window shown")
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
