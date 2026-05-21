"""Download queue status panel."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStyle,
    QVBoxLayout,
    QWidget,
)

QUEUE_BODY_MIN_HEIGHT = 104
QUEUE_BODY_MAX_HEIGHT = 170
QUEUE_ROW_MIN_HEIGHT = 34


class DownloadQueueRow(QWidget):
    cancel_requested = Signal(str)
    retry_requested = Signal(str)
    remove_requested = Signal(str)

    def __init__(self, video_id: str, tr: Callable[[str], str]) -> None:
        super().__init__()
        self.video_id = video_id
        self.tr_text = tr
        self.state = "queued"
        self._hovered = False
        self.setObjectName("queueRow")
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setMinimumHeight(QUEUE_ROW_MIN_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        row_layout = QHBoxLayout(self)
        row_layout.setContentsMargins(8, 4, 6, 4)
        row_layout.setSpacing(10)

        self.label = QLabel()
        self.label.setMinimumWidth(260)
        self.label.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("0.0%")
        self.progress.setTextVisible(True)
        self.progress.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.actions = QWidget()
        self.actions.setFixedWidth(84)
        self.actions.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        actions_layout = QHBoxLayout(self.actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(4)

        self.cancel_button = self._make_icon_button(
            QStyle.StandardPixmap.SP_DialogCancelButton,
            tr("queue.cancel"),
        )
        self.retry_button = self._make_icon_button(
            QStyle.StandardPixmap.SP_MediaPlay,
            tr("queue.restart"),
        )
        trash_icon = getattr(
            QStyle.StandardPixmap,
            "SP_TrashIcon",
            QStyle.StandardPixmap.SP_DialogDiscardButton,
        )
        self.remove_button = self._make_icon_button(trash_icon, tr("queue.remove"))

        self.cancel_button.clicked.connect(lambda: self.cancel_requested.emit(self.video_id))
        self.retry_button.clicked.connect(lambda: self.retry_requested.emit(self.video_id))
        self.remove_button.clicked.connect(lambda: self.remove_requested.emit(self.video_id))

        actions_layout.addWidget(self.cancel_button)
        actions_layout.addWidget(self.retry_button)
        actions_layout.addWidget(self.remove_button)

        row_layout.addWidget(self.label, 0)
        row_layout.addWidget(self.progress, 1)
        row_layout.addWidget(self.actions, 0)
        self._sync_actions()

    def _make_icon_button(self, icon: QStyle.StandardPixmap, tooltip: str) -> QPushButton:
        button = QPushButton()
        button.setObjectName("queueActionButton")
        button.setIcon(self.style().standardIcon(icon))
        button.setToolTip(tooltip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedSize(24, 24)
        button.setFlat(True)
        return button

    def enterEvent(self, event) -> None:  # noqa: ANN001
        self._hovered = True
        self._sync_actions()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: ANN001
        self._hovered = False
        self._sync_actions()
        super().leaveEvent(event)

    def set_status(self, text: str, percent: float | None, state: str | None) -> None:
        self.label.setText(text)
        if state is not None:
            self.state = state
        if percent is not None:
            bounded = max(0.0, min(100.0, percent))
            self.progress.setValue(int(round(bounded)))
            self.progress.setFormat(f"{bounded:.1f}%")
        self._sync_actions()

    def _sync_actions(self) -> None:
        show_cancel = self._hovered and self.state == "downloading"
        show_retry = self._hovered and self.state in {"canceled", "failed"}
        show_remove = self._hovered and self.state in {"queued", "canceled", "failed"}
        self.cancel_button.setVisible(show_cancel)
        self.retry_button.setVisible(show_retry)
        self.remove_button.setVisible(show_remove)


class DownloadQueuePanel(QWidget):
    cancel_requested = Signal(str)
    retry_requested = Signal(str)
    remove_requested = Signal(str)

    def __init__(self, tr: Callable[[str], str]) -> None:
        super().__init__()
        self.tr_text = tr
        self._rows: dict[str, DownloadQueueRow] = {}
        self.setMinimumHeight(QUEUE_BODY_MIN_HEIGHT + 28)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel(tr("queue.title"))
        title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(title)

        self.queue_frame = QFrame()
        self.queue_frame.setObjectName("queueGlass")
        self.queue_frame.setMinimumHeight(QUEUE_BODY_MIN_HEIGHT)
        self.queue_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        self.queue_layout = QVBoxLayout(self.queue_frame)
        self.queue_layout.setContentsMargins(8, 6, 8, 6)
        self.queue_layout.setSpacing(4)
        self.empty_label: QLabel | None = QLabel(tr("queue.empty"))
        self.queue_layout.addWidget(self.empty_label)
        self.queue_layout.addStretch()

        self.queue_scroll = QScrollArea()
        self.queue_scroll.setObjectName("queueScroll")
        self.queue_scroll.setWidgetResizable(True)
        self.queue_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.queue_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.queue_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.queue_scroll.setMinimumHeight(QUEUE_BODY_MIN_HEIGHT)
        self.queue_scroll.setMaximumHeight(QUEUE_BODY_MAX_HEIGHT)
        self.queue_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.queue_scroll.setWidget(self.queue_frame)
        layout.addWidget(self.queue_scroll)

    def _add_before_stretch(self, widget: QWidget) -> None:
        stretch = (
            self.queue_layout.takeAt(self.queue_layout.count() - 1)
            if self.queue_layout.count()
            else None
        )
        self.queue_layout.addWidget(widget)
        if stretch is not None:
            self.queue_layout.addItem(stretch)

    def reset(self) -> None:
        self._rows.clear()
        while self.queue_layout.count():
            item = self.queue_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.empty_label = QLabel(self.tr_text("queue.empty"))
        self.queue_layout.addWidget(self.empty_label)
        self.queue_layout.addStretch()

    def set_job(
        self,
        video_id: str,
        text: str,
        percent: float | None = None,
        state: str | None = None,
    ) -> None:
        if video_id not in self._rows:
            if self.empty_label is not None:
                self.queue_layout.removeWidget(self.empty_label)
                self.empty_label.deleteLater()
                self.empty_label = None
            row = DownloadQueueRow(video_id, self.tr_text)
            row.cancel_requested.connect(self.cancel_requested.emit)
            row.retry_requested.connect(self.retry_requested.emit)
            row.remove_requested.connect(self.remove_requested.emit)
            self._add_before_stretch(row)
            self._rows[video_id] = row

        self._rows[video_id].set_status(text, percent, state)

    def remove_job(self, video_id: str) -> None:
        row = self._rows.pop(video_id, None)
        if row is not None:
            self.queue_layout.removeWidget(row)
            row.deleteLater()
        if not self._rows and self.empty_label is None:
            self.empty_label = QLabel(self.tr_text("queue.empty"))
            self._add_before_stretch(self.empty_label)
