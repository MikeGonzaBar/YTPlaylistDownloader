"""About dialog."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from playlist_folder_downloader.constants import APP_NAME, APP_VERSION
from playlist_folder_downloader.services.dependency_checker import DependencyStatus


class AboutDialog(QDialog):
    def __init__(
        self,
        tr: Callable[[str], str],
        dependency_status: DependencyStatus,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("about.title"))
        layout = QVBoxLayout(self)
        title = QLabel(f"{APP_NAME} {APP_VERSION}")
        layout.addWidget(title)
        notice = QLabel(tr("about.notice"))
        notice.setWordWrap(True)
        layout.addWidget(notice)
        limitations = QLabel(tr("about.limitations"))
        limitations.setWordWrap(True)
        layout.addWidget(limitations)
        deps = QLabel(
            "\n".join(
                [
                    f"yt-dlp: {dependency_status.yt_dlp_version or 'missing'}",
                    f"FFmpeg: {dependency_status.ffmpeg_path or 'missing'}",
                    f"ffprobe: {dependency_status.ffprobe_path or 'missing'}",
                    f"JavaScript runtime: {dependency_status.js_runtime_name or 'missing'}"
                    f"{f' ({dependency_status.js_runtime_path})' if dependency_status.js_runtime_path else ''}",
                ]
            )
        )
        layout.addWidget(deps)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
