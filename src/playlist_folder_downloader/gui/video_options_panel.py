"""Per-video and bulk options panel."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from playlist_folder_downloader.constants import SUPPORTED_CONTAINERS, SUPPORTED_QUALITY_LABELS
from playlist_folder_downloader.gui.widgets import parse_language_list
from playlist_folder_downloader.models import VideoDownloadOptions, VideoInfo
from playlist_folder_downloader.services.format_selector import quality_label_to_height


class VideoOptionsPanel(QWidget):
    probe_requested = Signal(object)

    def __init__(self, tr: Callable[[str], str]) -> None:
        super().__init__()
        self.tr_text = tr
        self._current_videos: list[VideoInfo] = []
        self._loading = False

        root = QVBoxLayout(self)
        self.title = QLabel(tr("options.title"))
        root.addWidget(self.title)

        self.message = QLabel(tr("options.none"))
        self.message.setWordWrap(True)
        root.addWidget(self.message)

        self.form_widget = QWidget()
        form = QFormLayout(self.form_widget)

        self.include_video = QCheckBox(tr("options.include_video"))
        self.include_audio = QCheckBox(tr("options.include_audio"))
        include_row = QHBoxLayout()
        include_row.addWidget(self.include_video)
        include_row.addWidget(self.include_audio)
        form.addRow("", include_row)

        self.quality = QComboBox()
        for label in SUPPORTED_QUALITY_LABELS:
            self.quality.addItem(self._quality_text(label), label)
        form.addRow(tr("options.quality"), self.quality)

        self.video_formats = QListWidget()
        self.video_formats.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.video_formats.setMinimumHeight(90)
        form.addRow(tr("options.video_formats"), self.video_formats)

        self.audio_tracks = QListWidget()
        self.audio_tracks.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.audio_tracks.setMinimumHeight(110)
        form.addRow(tr("options.audio_tracks"), self.audio_tracks)

        self.probe_button = QPushButton(tr("options.probe"))
        form.addRow("", self.probe_button)

        self.subtitles_enabled = QCheckBox(tr("options.subtitles"))
        self.manual_subtitles = QCheckBox(tr("options.manual_subtitles"))
        self.auto_subtitles = QCheckBox(tr("options.auto_subtitles"))
        form.addRow("", self.subtitles_enabled)
        form.addRow("", self.manual_subtitles)
        form.addRow("", self.auto_subtitles)

        self.subtitle_languages = QComboBox()
        self.subtitle_languages.setEditable(True)
        self.subtitle_languages.addItems(["en", "es", "en,es"])
        form.addRow(tr("options.subtitle_languages"), self.subtitle_languages)

        self.embed_subtitles = QCheckBox(tr("options.embed_subtitles"))
        self.keep_subtitle_files = QCheckBox(tr("options.keep_subtitle_files"))
        form.addRow("", self.embed_subtitles)
        form.addRow("", self.keep_subtitle_files)

        self.container = QComboBox()
        self.container.addItems(SUPPORTED_CONTAINERS)
        form.addRow(tr("options.container"), self.container)

        self.mkv_note = QLabel(tr("options.mkv_required"))
        self.mkv_note.setWordWrap(True)
        form.addRow("", self.mkv_note)

        root.addWidget(self.form_widget)
        root.addStretch()

        self.probe_button.clicked.connect(self._request_probe)
        self.subtitles_enabled.toggled.connect(self._enforce_container)
        self.embed_subtitles.toggled.connect(self._enforce_container)
        self.audio_tracks.itemSelectionChanged.connect(self._enforce_container)
        self.quality.currentIndexChanged.connect(self._quality_changed)

        self.set_selection([], None)

    def _quality_text(self, label: str) -> str:
        key = {
            "Best": "quality.best",
            "2160p": "quality.2160p",
            "1440p": "quality.1440p",
            "1080p": "quality.1080p",
            "720p": "quality.720p",
            "480p": "quality.480p",
            "Audio only": "quality.audio_only",
            "Custom": "quality.custom",
        }.get(label, label)
        return self.tr_text(key)

    def set_selection(self, videos: list[VideoInfo], options: VideoDownloadOptions | None) -> None:
        self._current_videos = videos
        self._loading = True
        enabled = bool(videos)
        self.form_widget.setEnabled(enabled)
        if not videos:
            self.message.setText(self.tr_text("options.none"))
        elif len(videos) > 1:
            self.message.setText(self.tr_text("options.multiple"))
        else:
            self.message.setText(videos[0].title)

        options = deepcopy(options) if options is not None else VideoDownloadOptions()
        self.include_video.setChecked(options.include_video)
        self.include_audio.setChecked(options.include_audio)
        self._set_quality_from_options(options)
        self.subtitles_enabled.setChecked(options.subtitles_enabled)
        self.manual_subtitles.setChecked(options.include_manual_subtitles)
        self.auto_subtitles.setChecked(options.include_auto_subtitles)
        self.subtitle_languages.setEditText(",".join(options.subtitle_languages or ["en"]))
        self.embed_subtitles.setChecked(options.embed_subtitles)
        self.keep_subtitle_files.setChecked(options.keep_subtitle_files)
        self.container.setCurrentText(options.prefer_container)
        self._populate_format_lists(videos[0] if len(videos) == 1 else None, options)
        self._loading = False
        self._enforce_container()

    def _set_quality_from_options(self, options: VideoDownloadOptions) -> None:
        if not options.include_video and options.include_audio:
            wanted = "Audio only"
        elif options.max_height is None:
            wanted = "Best"
        else:
            wanted = f"{options.max_height}p"
        index = self.quality.findData(wanted)
        self.quality.setCurrentIndex(index if index >= 0 else self.quality.findData("Custom"))

    def _populate_format_lists(
        self,
        video: VideoInfo | None,
        options: VideoDownloadOptions,
    ) -> None:
        self.video_formats.clear()
        self.audio_tracks.clear()
        if video is None or not video.formats:
            return
        for media_format in video.formats:
            if media_format.is_video:
                parts = [
                    media_format.resolution or "",
                    media_format.vcodec or "",
                    f"{media_format.fps:g}fps" if media_format.fps else "",
                    media_format.ext or "",
                    media_format.format_id,
                ]
                label = " | ".join(part for part in parts if part)
                item = QListWidgetItem(label)
                item.setData(256, media_format.format_id)
                self.video_formats.addItem(item)
                if media_format.format_id == options.selected_video_format_id:
                    item.setSelected(True)
            if media_format.is_audio:
                parts = [
                    media_format.language or "und",
                    media_format.acodec or "",
                    f"{media_format.abr:g}kbps" if media_format.abr else "",
                    media_format.format_id,
                ]
                label = " | ".join(part for part in parts if part)
                item = QListWidgetItem(label)
                item.setData(256, media_format.format_id)
                self.audio_tracks.addItem(item)
                if media_format.format_id in options.selected_audio_format_ids:
                    item.setSelected(True)

    def _request_probe(self) -> None:
        if len(self._current_videos) == 1:
            self.probe_requested.emit(self._current_videos[0])

    def _quality_changed(self) -> None:
        if self._loading:
            return
        if self.quality.currentData() == "Audio only":
            self.include_video.setChecked(False)
            self.include_audio.setChecked(True)

    def _enforce_container(self) -> None:
        selected_audio_count = len(self.audio_tracks.selectedItems())
        needs_mkv = selected_audio_count > 1 or (
            self.subtitles_enabled.isChecked() and self.embed_subtitles.isChecked()
        )
        if needs_mkv:
            self.container.setCurrentText("mkv")
        self.mkv_note.setVisible(needs_mkv)

    def current_options(self) -> VideoDownloadOptions:
        quality_label = str(self.quality.currentData() or "1080p")
        include_video = self.include_video.isChecked()
        include_audio = self.include_audio.isChecked()
        if quality_label == "Audio only":
            include_video = False
            include_audio = True
        selected_audio = [
            str(item.data(256))
            for item in self.audio_tracks.selectedItems()
            if item.data(256)
        ]
        selected_video_items = self.video_formats.selectedItems()
        selected_video = (
            str(selected_video_items[0].data(256))
            if selected_video_items and selected_video_items[0].data(256)
            else None
        )
        return VideoDownloadOptions(
            include_video=include_video,
            include_audio=include_audio,
            max_height=quality_label_to_height(quality_label),
            selected_video_format_id=selected_video,
            selected_audio_format_ids=selected_audio,
            allow_multiple_audio_tracks=len(selected_audio) > 1,
            prefer_container=self.container.currentText(),
            subtitles_enabled=self.subtitles_enabled.isChecked(),
            include_manual_subtitles=self.manual_subtitles.isChecked(),
            include_auto_subtitles=self.auto_subtitles.isChecked(),
            subtitle_languages=parse_language_list(self.subtitle_languages.currentText()),
            embed_subtitles=self.embed_subtitles.isChecked(),
            keep_subtitle_files=self.keep_subtitle_files.isChecked(),
        )
