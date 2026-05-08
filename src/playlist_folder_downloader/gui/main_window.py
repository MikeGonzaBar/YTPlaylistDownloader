"""Main application window."""

from __future__ import annotations

import time
from copy import deepcopy
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
)

from playlist_folder_downloader.diagnostics import debug_print
from playlist_folder_downloader.gui.about_dialog import AboutDialog
from playlist_folder_downloader.gui.download_queue_panel import DownloadQueuePanel
from playlist_folder_downloader.gui.playlist_table import PlaylistTable
from playlist_folder_downloader.gui.settings_dialog import SettingsDialog
from playlist_folder_downloader.gui.style import LiquidGlassRoot, prepare_liquid_glass_window
from playlist_folder_downloader.gui.video_options_panel import VideoOptionsPanel
from playlist_folder_downloader.i18n.translation_manager import TranslationManager
from playlist_folder_downloader.models import (
    DownloadJob,
    PlaylistInfo,
    VideoDownloadOptions,
    VideoInfo,
)
from playlist_folder_downloader.services.dependency_checker import (
    DependencyStatus,
    check_dependencies,
)
from playlist_folder_downloader.services.download_service import make_download_filename_preview
from playlist_folder_downloader.services.format_selector import quality_label_to_height
from playlist_folder_downloader.settings import AppSettings, save_settings
from playlist_folder_downloader.utils.filenames import make_playlist_folder_name
from playlist_folder_downloader.utils.url_utils import is_probably_youtube_media_url
from playlist_folder_downloader.workers.download_worker import DownloadWorker
from playlist_folder_downloader.workers.playlist_loader_worker import PlaylistLoaderWorker
from playlist_folder_downloader.workers.video_probe_worker import VideoProbeWorker


class MainWindow(QMainWindow):
    cancel_downloads_requested = Signal()

    def __init__(
        self,
        settings: AppSettings,
        translations: TranslationManager,
        dependency_status: DependencyStatus,
    ) -> None:
        super().__init__()
        self.settings = settings
        self.translations = translations
        self.dependency_status = dependency_status
        self.playlist: PlaylistInfo | None = None
        self.options_by_id: dict[str, VideoDownloadOptions] = {}
        self.statuses: dict[str, str] = {}
        self._playlist_thread: QThread | None = None
        self._playlist_worker: PlaylistLoaderWorker | None = None
        self._probe_thread: QThread | None = None
        self._probe_worker: VideoProbeWorker | None = None
        self._download_thread: QThread | None = None
        self._download_worker: DownloadWorker | None = None
        self._load_started_at: float | None = None
        self._last_load_print_second = -1
        self._load_timer = QTimer(self)
        self._load_timer.setInterval(1000)
        self._load_timer.timeout.connect(self._load_heartbeat)

        self.setWindowTitle(self.tr_text("app.title"))
        self.resize(1200, 760)
        prepare_liquid_glass_window(self)

        central = LiquidGlassRoot()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(10)

        input_row = QHBoxLayout()
        input_row.addWidget(QLabel(self.tr_text("playlist.url")))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(self.tr_text("playlist.url.placeholder"))
        input_row.addWidget(self.url_input, 1)
        self.load_button = QPushButton(self.tr_text("playlist.load"))
        self.settings_button = QPushButton(self.tr_text("settings.open"))
        self.about_button = QPushButton(self.tr_text("about.open"))
        input_row.addWidget(self.load_button)
        input_row.addWidget(self.settings_button)
        input_row.addWidget(self.about_button)
        root.addLayout(input_row)

        info_row = QHBoxLayout()
        self.playlist_title = QLabel(self.tr_text("playlist.title.placeholder"))
        self.video_count = QLabel(self.tr_text("playlist.count").format(count=0))
        self.dependency_warning = QLabel(self._dependency_text())
        self.dependency_warning.setWordWrap(True)
        info_row.addWidget(self.playlist_title, 2)
        info_row.addWidget(self.video_count)
        info_row.addWidget(self.dependency_warning, 2)
        root.addLayout(info_row)

        splitter = QSplitter()
        self.playlist_table = PlaylistTable(self.tr_text)
        self.options_panel = VideoOptionsPanel(self.tr_text)
        splitter.addWidget(self.playlist_table)
        splitter.addWidget(self.options_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter, 1)

        self.queue_panel = DownloadQueuePanel(self.tr_text)
        root.addWidget(self.queue_panel)

        action_row = QHBoxLayout()
        self.select_all_button = QPushButton(self.tr_text("actions.select_all"))
        self.deselect_all_button = QPushButton(self.tr_text("actions.deselect_all"))
        action_row.addWidget(self.select_all_button)
        action_row.addWidget(self.deselect_all_button)
        action_row.addStretch()
        self.apply_selected_button = QPushButton(self.tr_text("actions.apply_selected"))
        self.apply_all_button = QPushButton(self.tr_text("actions.apply_all"))
        self.download_selected_button = QPushButton(self.tr_text("actions.download_selected"))
        self.cancel_button = QPushButton(self.tr_text("actions.cancel"))
        action_row.addWidget(self.apply_selected_button)
        action_row.addWidget(self.apply_all_button)
        action_row.addWidget(self.download_selected_button)
        action_row.addWidget(self.cancel_button)
        root.addLayout(action_row)

        self.load_button.clicked.connect(self.load_playlist)
        self.settings_button.clicked.connect(self.open_settings)
        self.about_button.clicked.connect(self.open_about)
        self.select_all_button.clicked.connect(self.select_all_videos)
        self.deselect_all_button.clicked.connect(self.deselect_all_videos)
        self.playlist_table.selection_changed.connect(self._selection_changed)
        self.options_panel.probe_requested.connect(self._start_probe)
        self.apply_selected_button.clicked.connect(self.apply_options_to_selected)
        self.apply_all_button.clicked.connect(self.apply_options_to_all)
        self.download_selected_button.clicked.connect(self.download_selected)
        self.cancel_button.clicked.connect(self.cancel_downloads_requested.emit)

    def tr_text(self, key: str) -> str:
        return self.translations.tr(key)

    def _dependency_text(self) -> str:
        if not self.dependency_status.warnings:
            return self.tr_text("dependencies.ok")
        return f"{self.tr_text('dependencies.warning')}: {' '.join(self.dependency_status.warnings)}"

    def _default_options(self) -> VideoDownloadOptions:
        quality = self.settings.default_quality
        return VideoDownloadOptions(
            include_video=self.settings.default_include_video and quality != "Audio only",
            include_audio=self.settings.default_include_audio,
            max_height=quality_label_to_height(quality),
            subtitles_enabled=self.settings.default_subtitles_enabled,
            subtitle_languages=list(self.settings.default_subtitle_languages),
        )

    def load_playlist(self) -> None:
        url = self.url_input.text().strip()
        if not is_probably_youtube_media_url(url):
            self._show_error(self.tr_text("error.invalid_url"))
            return
        debug_print("load button clicked")
        self.load_button.setEnabled(False)
        self.playlist_title.setText(self.tr_text("status.loading"))
        self._load_started_at = time.monotonic()
        self._last_load_print_second = -1
        self._load_timer.start()
        worker = PlaylistLoaderWorker(url)
        thread = QThread(self)
        self._playlist_thread = thread
        self._playlist_worker = worker
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.message.connect(self._playlist_message)
        worker.finished.connect(self._playlist_loaded)
        worker.failed.connect(self._playlist_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self.load_button.setEnabled(True))
        thread.finished.connect(self._playlist_thread_finished)
        thread.start()

    def _playlist_loaded(self, playlist: PlaylistInfo) -> None:
        self._load_timer.stop()
        self._load_started_at = None
        self.playlist = playlist
        self.options_by_id = {video.id: self._default_options() for video in playlist.videos}
        self.statuses = {video.id: self.tr_text("status.ready") for video in playlist.videos}
        self.playlist_title.setText(playlist.title)
        count_text = self.tr_text("playlist.count").format(count=len(playlist.videos))
        if playlist.warning_count:
            warning = self.tr_text("playlist.warning.unavailable").format(count=playlist.warning_count)
            count_text = f"{count_text} | {warning}"
        self.video_count.setText(count_text)
        self.playlist_table.set_playlist(playlist.videos, self.options_by_id, self.statuses)
        self.queue_panel.reset()
        debug_print(f"GUI loaded collection: {playlist.title!r} ({len(playlist.videos)} video(s))")

    def _playlist_failed(self, error: str) -> None:
        self._load_timer.stop()
        self._load_started_at = None
        self.playlist_title.setText(self.tr_text("playlist.title.placeholder"))
        debug_print(f"GUI load failed: {error}")
        self._show_error(error)

    def _playlist_message(self, message: str) -> None:
        self.playlist_title.setText(message)
        debug_print(f"worker message: {message}")

    def _playlist_thread_finished(self) -> None:
        debug_print("playlist thread cleaned up")
        self._playlist_worker = None
        self._playlist_thread = None

    def _load_heartbeat(self) -> None:
        if self._load_started_at is None:
            return
        elapsed = int(time.monotonic() - self._load_started_at)
        self.playlist_title.setText(self.tr_text("playlist.loading_elapsed").format(seconds=elapsed))
        if elapsed >= 1 and elapsed % 5 == 0 and elapsed != self._last_load_print_second:
            self._last_load_print_second = elapsed
            debug_print(f"still loading metadata after {elapsed}s")

    def _selection_changed(self) -> None:
        selected = self.playlist_table.selected_videos()
        options = self.options_by_id.get(selected[0].id) if selected else None
        self.options_panel.set_selection(selected, options)

    def _start_probe(self, video: VideoInfo) -> None:
        debug_print(f"probe requested: {video.id}")
        self.statuses[video.id] = self.tr_text("status.probing")
        self.playlist_table.update_status(video.id, self.statuses[video.id])
        worker = VideoProbeWorker(video)
        thread = QThread(self)
        self._probe_thread = thread
        self._probe_worker = worker
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._video_probed)
        worker.failed.connect(self._video_probe_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._probe_thread_finished)
        thread.start()

    def _video_probed(self, video: VideoInfo) -> None:
        if self.playlist is None:
            return
        for index, existing in enumerate(self.playlist.videos):
            if existing.id == video.id:
                self.playlist.videos[index] = video
                break
        self.statuses[video.id] = self.tr_text("status.ready")
        self.playlist_table.update_video(video)
        self.playlist_table.update_status(video.id, self.statuses[video.id])
        self._selection_changed()
        debug_print(f"GUI probe complete: {video.id}")

    def _video_probe_failed(self, video_id: str, error: str) -> None:
        self.statuses[video_id] = self.tr_text("status.failed")
        self.playlist_table.update_status(video_id, self.statuses[video_id])
        debug_print(f"GUI probe failed: {video_id}: {error}")
        self._show_error(error)

    def _probe_thread_finished(self) -> None:
        debug_print("probe thread cleaned up")
        self._probe_worker = None
        self._probe_thread = None

    def apply_options_to_selected(self) -> None:
        selected = self.playlist_table.selected_videos()
        if not selected:
            self._show_error(self.tr_text("error.no_selection"))
            return
        options = self.options_panel.current_options()
        for video in selected:
            self.options_by_id[video.id] = deepcopy(options)
            self.playlist_table.update_options_summary(video.id, self.options_by_id[video.id])

    def select_all_videos(self) -> None:
        self.playlist_table.set_all_checked(True)

    def deselect_all_videos(self) -> None:
        self.playlist_table.set_all_checked(False)

    def apply_options_to_all(self) -> None:
        if self.playlist is None:
            self._show_error(self.tr_text("error.no_playlist"))
            return
        options = self.options_panel.current_options()
        for video in self.playlist.videos:
            self.options_by_id[video.id] = deepcopy(options)
            self.playlist_table.update_options_summary(video.id, self.options_by_id[video.id])

    def download_selected(self) -> None:
        if self.playlist is None:
            self._show_error(self.tr_text("error.no_playlist"))
            return
        ids = self.playlist_table.checked_video_ids()
        if not ids:
            self._show_error(self.tr_text("error.no_selection"))
            return
        root = Path(self.settings.download_root).expanduser()
        if not root.exists():
            self._show_error(self.tr_text("error.download_root"))
            return
        output_dir = root / make_playlist_folder_name(self.playlist.title, self.playlist.id)
        videos_by_id = {video.id: video for video in self.playlist.videos}
        jobs: list[DownloadJob] = []
        for video_id in ids:
            if video_id not in videos_by_id:
                continue
            job = DownloadJob(
                video=videos_by_id[video_id],
                options=deepcopy(self.options_by_id[video_id]),
                output_dir=output_dir,
                status="queued",
                progress=0.0,
                message=None,
            )
            job.message = make_download_filename_preview(job)
            jobs.append(job)
        if not jobs:
            self._show_error(self.tr_text("error.no_selection"))
            return

        debug_print(f"starting download queue: {len(jobs)} job(s), output_dir={output_dir}")
        self.queue_panel.reset()
        worker = DownloadWorker(jobs, self.settings.max_concurrent_downloads)
        thread = QThread(self)
        self._download_worker = worker
        self._download_thread = thread
        worker.moveToThread(thread)
        self.cancel_downloads_requested.connect(worker.cancel_all, Qt.ConnectionType.DirectConnection)
        thread.started.connect(worker.run)
        worker.job_started.connect(self._download_started)
        worker.job_progress.connect(self._download_progress)
        worker.job_finished.connect(self._download_finished)
        worker.job_failed.connect(self._download_failed)
        worker.job_canceled.connect(self._download_canceled)
        worker.all_finished.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._download_thread_finished)
        thread.start()

    def _download_started(self, video_id: str) -> None:
        self.statuses[video_id] = self.tr_text("status.downloading")
        self.playlist_table.update_status(video_id, self.statuses[video_id])
        self.queue_panel.set_job(
            video_id,
            f"{self._video_title(video_id)}: {self.tr_text('status.downloading')}",
            0,
        )

    def _download_progress(self, video_id: str, percent: float, speed_text: str, eta_text: str) -> None:
        details = " ".join(part for part in [f"{percent:5.1f}%", speed_text, eta_text] if part)
        self.queue_panel.set_job(video_id, f"{self._video_title(video_id)}: {details}", percent)

    def _download_finished(self, video_id: str, message: str) -> None:
        self.statuses[video_id] = self.tr_text("status.done")
        self.playlist_table.update_status(video_id, self.statuses[video_id])
        self.queue_panel.set_job(
            video_id,
            f"{self._video_title(video_id)}: {self.tr_text('status.done')} - {message}",
            100,
        )

    def _download_failed(self, video_id: str, error: str) -> None:
        self.statuses[video_id] = self.tr_text("status.failed")
        self.playlist_table.update_status(video_id, self.statuses[video_id])
        self.queue_panel.set_job(
            video_id,
            f"{self._video_title(video_id)}: {self.tr_text('status.failed')} - {error}",
            0,
        )

    def _download_canceled(self, video_id: str) -> None:
        self.statuses[video_id] = self.tr_text("status.canceled")
        self.playlist_table.update_status(video_id, self.statuses[video_id])
        self.queue_panel.set_job(video_id, f"{self._video_title(video_id)}: {self.tr_text('status.canceled')}", 0)

    def _download_thread_finished(self) -> None:
        self._download_worker = None
        self._download_thread = None

    def _video_title(self, video_id: str) -> str:
        if self.playlist is not None:
            for video in self.playlist.videos:
                if video.id == video_id:
                    return video.title
        return video_id

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self.tr_text, self)
        if dialog.exec():
            self.settings = dialog.selected_settings()
            save_settings(self.settings)
            self.dependency_status = check_dependencies(self.settings.ffmpeg_path)
            self.dependency_warning.setText(self._dependency_text())

    def open_about(self) -> None:
        dialog = AboutDialog(self.tr_text, self.dependency_status, self)
        dialog.exec()

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, self.tr_text("dialog.error"), message)
