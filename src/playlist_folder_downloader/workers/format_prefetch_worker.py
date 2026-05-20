"""Qt worker for prefetching detailed format metadata."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from playlist_folder_downloader.diagnostics import debug_print
from playlist_folder_downloader.models import VideoInfo
from playlist_folder_downloader.services.probe_service import probe_video


class FormatPrefetchWorker(QObject):
    message = Signal(str)
    video_ready = Signal(object, int)
    video_failed = Signal(str, str, int)
    completed = Signal(int)
    finished = Signal()

    def __init__(self, videos: list[VideoInfo], generation: int) -> None:
        super().__init__()
        self.videos = videos
        self.generation = generation
        self._stop_requested = False

    @Slot()
    def request_stop(self) -> None:
        self._stop_requested = True

    @Slot()
    def run(self) -> None:
        total = len(self.videos)
        debug_print(f"format prefetch worker started: {total} video(s)")
        for index, video in enumerate(self.videos, start=1):
            if self._stop_requested:
                break
            if video.probed and video.formats:
                self.video_ready.emit(video, self.generation)
                continue
            self.message.emit(f"Prefetching formats {index}/{total}...")
            try:
                probed = probe_video(video.webpage_url)
            except Exception as exc:  # noqa: BLE001 - worker reports per-video failures to GUI
                debug_print(f"format prefetch failed for {video.id}: {exc}")
                self.video_failed.emit(video.id, str(exc), self.generation)
                continue
            probed.playlist_index = video.playlist_index
            debug_print(f"format prefetch finished for {video.id}")
            self.video_ready.emit(probed, self.generation)
        debug_print("format prefetch worker finished")
        self.completed.emit(self.generation)
        self.finished.emit()
