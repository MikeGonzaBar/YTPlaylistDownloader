"""Qt worker for detailed video probing."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from playlist_folder_downloader.diagnostics import debug_print
from playlist_folder_downloader.models import VideoInfo
from playlist_folder_downloader.services.probe_service import probe_video


class VideoProbeWorker(QObject):
    finished = Signal(object)
    failed = Signal(str, str)

    def __init__(self, video: VideoInfo) -> None:
        super().__init__()
        self.video = video

    @Slot()
    def run(self) -> None:
        debug_print(f"probe worker started: {self.video.id}")
        try:
            probed = probe_video(self.video.webpage_url)
        except Exception as exc:  # noqa: BLE001 - worker reports all failures to GUI
            debug_print(f"probe worker failed for {self.video.id}: {exc}")
            self.failed.emit(self.video.id, str(exc))
            return
        probed.playlist_index = self.video.playlist_index
        debug_print(f"probe worker finished: {self.video.id}")
        self.finished.emit(probed)
