"""Qt worker for sequential download queues."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from playlist_folder_downloader.diagnostics import debug_print
from playlist_folder_downloader.models import DownloadJob
from playlist_folder_downloader.services.download_service import (
    DownloadCancelled,
    DownloadFailed,
    download_video,
)


class DownloadWorker(QObject):
    job_started = Signal(str)
    job_progress = Signal(str, float, str, str)
    job_finished = Signal(str, str)
    job_failed = Signal(str, str)
    job_canceled = Signal(str)
    all_finished = Signal()

    def __init__(self, jobs: list[DownloadJob], max_concurrent_downloads: int = 1) -> None:
        super().__init__()
        self.jobs = jobs
        self.max_concurrent_downloads = max(1, max_concurrent_downloads)
        self._cancel_all = False
        self._cancel_current = False

    @Slot()
    def run(self) -> None:
        debug_print(f"download worker started: {len(self.jobs)} job(s)")
        for job in self.jobs:
            video_id = job.video.id
            if self._cancel_all:
                self.job_canceled.emit(video_id)
                continue

            self._cancel_current = False
            debug_print(f"download job started: {video_id}")
            self.job_started.emit(video_id)
            final_filename = ""

            def callback(payload: dict, current_video_id: str = video_id) -> None:
                nonlocal final_filename
                total = payload.get("total_bytes") or payload.get("total_bytes_estimate") or 0
                downloaded = payload.get("downloaded_bytes") or 0
                percent = (float(downloaded) / float(total) * 100.0) if total else 0.0
                speed_text = payload.get("_speed_str") or ""
                eta_text = payload.get("_eta_str") or ""
                filename = payload.get("filename") or payload.get("tmpfilename")
                if filename:
                    final_filename = Path(str(filename)).name
                if payload.get("status") == "finished":
                    percent = 100.0
                self.job_progress.emit(current_video_id, percent, str(speed_text), str(eta_text))

            try:
                download_video(job, callback, self._is_cancel_requested)
            except DownloadCancelled:
                debug_print(f"download job canceled: {video_id}")
                self.job_canceled.emit(video_id)
            except DownloadFailed as exc:
                debug_print(f"download job failed: {video_id}: {exc}")
                self.job_failed.emit(video_id, str(exc))
            except Exception as exc:  # noqa: BLE001 - report per-video failure without crashing GUI
                debug_print(f"download job failed unexpectedly: {video_id}: {exc}")
                self.job_failed.emit(video_id, str(exc))
            else:
                debug_print(f"download job finished: {video_id}")
                self.job_finished.emit(video_id, final_filename or job.message or "Finished")
        debug_print("download worker finished")
        self.all_finished.emit()

    def _is_cancel_requested(self) -> bool:
        return self._cancel_all or self._cancel_current

    @Slot()
    def cancel_current(self) -> None:
        debug_print("cancel current requested")
        self._cancel_current = True

    @Slot()
    def cancel_all(self) -> None:
        debug_print("cancel all requested")
        self._cancel_all = True
        self._cancel_current = True
