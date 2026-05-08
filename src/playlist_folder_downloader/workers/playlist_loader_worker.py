"""Qt worker for loading playlist metadata off the main thread."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from playlist_folder_downloader.diagnostics import debug_print
from playlist_folder_downloader.services.playlist_service import load_playlist


class PlaylistLoaderWorker(QObject):
    started = Signal()
    message = Signal(str)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, playlist_url: str) -> None:
        super().__init__()
        self.playlist_url = playlist_url

    @Slot()
    def run(self) -> None:
        debug_print("playlist worker started")
        self.started.emit()
        self.message.emit("Loading playlist metadata...")
        try:
            self.message.emit("Requesting metadata from yt-dlp...")
            playlist = load_playlist(self.playlist_url)
        except Exception as exc:  # noqa: BLE001 - worker reports all failures to GUI
            debug_print(f"playlist worker failed: {exc}")
            self.failed.emit(str(exc))
            return
        debug_print(f"playlist worker finished: {len(playlist.videos)} video(s)")
        self.finished.emit(playlist)
