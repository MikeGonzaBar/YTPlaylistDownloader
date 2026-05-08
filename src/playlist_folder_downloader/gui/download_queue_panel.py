"""Download queue status panel."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget


class DownloadQueuePanel(QWidget):
    def __init__(self, tr: Callable[[str], str]) -> None:
        super().__init__()
        self.tr_text = tr
        self._rows: dict[str, tuple[QLabel, QProgressBar]] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel(tr("queue.title")))

        self.queue_frame = QFrame()
        self.queue_frame.setObjectName("queueGlass")
        self.queue_layout = QVBoxLayout(self.queue_frame)
        self.queue_layout.setContentsMargins(8, 6, 8, 6)
        self.queue_layout.setSpacing(4)
        self.empty_label = QLabel(tr("queue.empty"))
        self.queue_layout.addWidget(self.empty_label)
        layout.addWidget(self.queue_frame)

    def reset(self) -> None:
        self._rows.clear()
        while self.queue_layout.count():
            item = self.queue_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.empty_label = QLabel(self.tr_text("queue.empty"))
        self.queue_layout.addWidget(self.empty_label)

    def set_job(self, video_id: str, text: str, percent: float | None = None) -> None:
        if video_id not in self._rows:
            if self.empty_label is not None:
                self.empty_label.deleteLater()
                self.empty_label = None
            row = QWidget()
            row.setObjectName("queueRow")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(6, 3, 6, 3)
            row_layout.setSpacing(10)
            label = QLabel(text)
            label.setMinimumWidth(220)
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(0)
            progress.setTextVisible(False)
            row_layout.addWidget(label, 0)
            row_layout.addWidget(progress, 1)
            self.queue_layout.addWidget(row)
            self._rows[video_id] = (label, progress)
        else:
            label, progress = self._rows[video_id]
            label.setText(text)

        if percent is not None:
            _, progress = self._rows[video_id]
            progress.setValue(max(0, min(100, int(round(percent)))))
