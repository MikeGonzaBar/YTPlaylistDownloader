"""Settings dialog."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from playlist_folder_downloader.constants import SUPPORTED_QUALITY_LABELS
from playlist_folder_downloader.settings import AppSettings


class SettingsDialog(QDialog):
    def __init__(
        self,
        settings: AppSettings,
        tr: Callable[[str], str],
        detected_ffmpeg_path: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.tr_text = tr
        self.settings = deepcopy(settings)
        self.setWindowTitle(tr("settings.title"))

        root = QVBoxLayout(self)
        form = QFormLayout()
        root.addLayout(form)

        self.download_root = QLineEdit(self.settings.download_root)
        browse_button = QPushButton(tr("settings.choose"))
        browse_button.clicked.connect(self._choose_download_root)
        download_row = QHBoxLayout()
        download_row.addWidget(self.download_root)
        download_row.addWidget(browse_button)
        form.addRow(tr("settings.download_folder"), download_row)

        self.language = QComboBox()
        self.language.addItem(tr("settings.language.system"), None)
        self.language.addItem(tr("settings.language.en"), "en")
        self.language.addItem(tr("settings.language.es"), "es")
        current_language = self.settings.language
        for index in range(self.language.count()):
            if self.language.itemData(index) == current_language:
                self.language.setCurrentIndex(index)
                break
        form.addRow(tr("settings.language"), self.language)

        self.ffmpeg_path = QLineEdit(self.settings.ffmpeg_path or detected_ffmpeg_path or "")
        ffmpeg_button = QPushButton(tr("settings.choose"))
        ffmpeg_button.clicked.connect(self._choose_ffmpeg_path)
        ffmpeg_row = QHBoxLayout()
        ffmpeg_row.addWidget(self.ffmpeg_path)
        ffmpeg_row.addWidget(ffmpeg_button)
        form.addRow(tr("settings.ffmpeg_path"), ffmpeg_row)

        self.max_concurrent = QSpinBox()
        self.max_concurrent.setRange(1, 8)
        self.max_concurrent.setValue(self.settings.max_concurrent_downloads)
        form.addRow(tr("settings.max_concurrent"), self.max_concurrent)

        self.default_quality = QComboBox()
        self.default_quality.addItems(SUPPORTED_QUALITY_LABELS)
        self.default_quality.setCurrentText(self.settings.default_quality)
        form.addRow(tr("settings.default_quality"), self.default_quality)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText(tr("settings.save"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("settings.cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _choose_download_root(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self,
            self.tr_text("settings.download_folder"),
            self.download_root.text(),
        )
        if chosen:
            self.download_root.setText(chosen)

    def _choose_ffmpeg_path(self) -> None:
        chosen, _ = QFileDialog.getOpenFileName(
            self,
            self.tr_text("settings.ffmpeg_path"),
            self.ffmpeg_path.text(),
        )
        if chosen:
            self.ffmpeg_path.setText(chosen)

    def selected_settings(self) -> AppSettings:
        self.settings.download_root = self.download_root.text().strip()
        self.settings.language = self.language.currentData()
        self.settings.ffmpeg_path = self.ffmpeg_path.text().strip() or None
        self.settings.max_concurrent_downloads = self.max_concurrent.value()
        self.settings.default_quality = self.default_quality.currentText()
        return self.settings
