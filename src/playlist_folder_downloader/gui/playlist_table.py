"""Playlist table widget."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem

from playlist_folder_downloader.gui.widgets import format_duration
from playlist_folder_downloader.models import VideoDownloadOptions, VideoInfo


class PlaylistTable(QTableWidget):
    selection_changed = Signal()

    COL_SELECTED = 0
    COL_INDEX = 1
    COL_TITLE = 2
    COL_DURATION = 3
    COL_CHANNEL = 4
    COL_STATUS = 5
    COL_QUALITY = 6
    COL_AUDIO = 7
    COL_SUBTITLES = 8

    def __init__(self, tr: Callable[[str], str]) -> None:
        super().__init__(0, 9)
        self.tr_text = tr
        self._videos: list[VideoInfo] = []
        self._row_for_video: dict[str, int] = {}
        self.setHorizontalHeaderLabels(
            [
                tr("table.selected"),
                tr("table.index"),
                tr("table.title"),
                tr("table.duration"),
                tr("table.channel"),
                tr("table.status"),
                tr("table.quality"),
                tr("table.audio"),
                tr("table.subtitles"),
            ]
        )
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(30)
        self.horizontalHeader().setSectionResizeMode(self.COL_TITLE, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(self.COL_SELECTED, QHeaderView.ResizeMode.ResizeToContents)
        self.itemSelectionChanged.connect(self.selection_changed.emit)

    def set_playlist(
        self,
        videos: list[VideoInfo],
        options_by_id: dict[str, VideoDownloadOptions],
        statuses: dict[str, str],
    ) -> None:
        self._videos = videos
        self._row_for_video = {}
        self.setRowCount(len(videos))
        for row, video in enumerate(videos):
            self._row_for_video[video.id] = row
            selected_item = QTableWidgetItem()
            selected_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            selected_item.setCheckState(Qt.CheckState.Checked)
            self.setItem(row, self.COL_SELECTED, selected_item)
            self.setItem(row, self.COL_INDEX, QTableWidgetItem(f"{video.playlist_index or row + 1:02d}"))
            self.setItem(row, self.COL_TITLE, QTableWidgetItem(video.title))
            self.setItem(row, self.COL_DURATION, QTableWidgetItem(format_duration(video.duration)))
            self.setItem(row, self.COL_CHANNEL, QTableWidgetItem(video.channel or ""))
            self.setItem(row, self.COL_STATUS, QTableWidgetItem(statuses.get(video.id, self.tr_text("status.ready"))))
            self.setItem(row, self.COL_QUALITY, QTableWidgetItem(""))
            self.setItem(row, self.COL_AUDIO, QTableWidgetItem(""))
            self.setItem(row, self.COL_SUBTITLES, QTableWidgetItem(""))
            self.update_options_summary(video.id, options_by_id[video.id])
        self.resizeColumnsToContents()

    def selected_videos(self) -> list[VideoInfo]:
        rows = sorted({index.row() for index in self.selectedIndexes()})
        return [self._videos[row] for row in rows if 0 <= row < len(self._videos)]

    def checked_video_ids(self) -> list[str]:
        ids: list[str] = []
        for video in self._videos:
            row = self._row_for_video.get(video.id)
            item = self.item(row, self.COL_SELECTED) if row is not None else None
            if item and item.checkState() == Qt.CheckState.Checked:
                ids.append(video.id)
        return ids

    def set_all_checked(self, checked: bool) -> None:
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for row in range(self.rowCount()):
            item = self.item(row, self.COL_SELECTED)
            if item is not None:
                item.setCheckState(state)

    def update_video(self, video: VideoInfo) -> None:
        row = self._row_for_video.get(video.id)
        if row is None:
            return
        self._videos[row] = video
        self.item(row, self.COL_TITLE).setText(video.title)
        self.item(row, self.COL_DURATION).setText(format_duration(video.duration))
        self.item(row, self.COL_CHANNEL).setText(video.channel or "")

    def update_status(self, video_id: str, status: str) -> None:
        row = self._row_for_video.get(video_id)
        if row is not None and self.item(row, self.COL_STATUS):
            self.item(row, self.COL_STATUS).setText(status)

    def update_options_summary(self, video_id: str, options: VideoDownloadOptions) -> None:
        row = self._row_for_video.get(video_id)
        if row is None:
            return
        quality = "Best" if options.max_height is None else f"{options.max_height}p"
        if not options.include_video and options.include_audio:
            quality = self.tr_text("quality.audio_only")
        audio = self.tr_text("options.include_audio") if options.include_audio else ""
        if len(options.selected_audio_format_ids) > 1:
            audio = f"{audio} ({len(options.selected_audio_format_ids)})"
        subtitles = self.tr_text("options.subtitles") if options.subtitles_enabled else ""
        self.item(row, self.COL_QUALITY).setText(quality)
        self.item(row, self.COL_AUDIO).setText(audio)
        self.item(row, self.COL_SUBTITLES).setText(subtitles)
