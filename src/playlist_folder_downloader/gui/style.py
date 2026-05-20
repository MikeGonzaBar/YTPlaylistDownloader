"""Application visual styling."""

from __future__ import annotations

import sys

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import (
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPalette,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget


class LiquidGlassRoot(QWidget):
    """Painted translucent acrylic background for the main app surface."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("glassRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def paintEvent(self, event) -> None:  # noqa: ANN001
        super().paintEvent(event)
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        path = QPainterPath()
        path.addRoundedRect(rect, 18, 18)
        painter.setClipPath(path)

        base = QLinearGradient(rect.topLeft(), rect.bottomRight())
        base.setColorAt(0.00, QColor(67, 68, 70, 220))
        base.setColorAt(0.34, QColor(43, 44, 46, 226))
        base.setColorAt(0.68, QColor(34, 35, 37, 228))
        base.setColorAt(1.00, QColor(79, 80, 83, 218))
        painter.fillPath(path, base)

        overlays = [
            (QPointF(rect.width() * 0.14, rect.height() * 0.10), rect.width() * 0.62, QColor(255, 255, 255, 42)),
            (QPointF(rect.width() * 0.88, rect.height() * 0.18), rect.width() * 0.52, QColor(210, 216, 232, 30)),
            (QPointF(rect.width() * 0.56, rect.height() * 0.92), rect.width() * 0.72, QColor(0, 0, 0, 62)),
        ]
        for center, radius, color in overlays:
            gradient = QRadialGradient(center, radius)
            gradient.setColorAt(0.0, color)
            gradient.setColorAt(0.55, QColor(color.red(), color.green(), color.blue(), max(8, color.alpha() // 2)))
            gradient.setColorAt(1.0, QColor(color.red(), color.green(), color.blue(), 0))
            painter.fillPath(path, gradient)

        sheen = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        sheen.setColorAt(0.0, QColor(255, 255, 255, 48))
        sheen.setColorAt(0.18, QColor(255, 255, 255, 16))
        sheen.setColorAt(1.0, QColor(255, 255, 255, 2))
        painter.fillPath(path, sheen)

        painter.setClipping(False)
        painter.setPen(QPen(QColor(255, 255, 255, 78), 1))
        painter.drawRoundedRect(rect, 18, 18)


def apply_liquid_glass_style(app: QApplication) -> None:
    """Apply a macOS/WinUI-inspired translucent glass style.

    Qt Widgets does not expose platform blur materials directly, so this uses
    supported Qt painting and stylesheets for translucent surfaces, compact
    controls, and restrained acrylic-style contrast across desktop platforms.
    """

    if sys.platform.startswith("linux"):
        app.setStyle("Fusion")

    palette = app.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor(32, 33, 35, 220))
    palette.setColor(QPalette.ColorRole.Base, QColor(36, 37, 39, 205))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(48, 49, 51, 205))
    palette.setColor(QPalette.ColorRole.Text, QColor(246, 247, 248))
    palette.setColor(QPalette.ColorRole.Button, QColor(58, 59, 62, 215))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(138, 142, 158, 220))
    app.setPalette(palette)

    app.setStyleSheet(
        """
        QMainWindow {
            background: transparent;
        }

        QWidget#glassRoot {
            background: transparent;
        }

        QLabel {
            color: rgba(248, 248, 250, 238);
            background: transparent;
        }

        QLineEdit,
        QComboBox,
        QSpinBox {
            min-height: 26px;
            padding: 3px 10px;
            color: rgba(248, 248, 250, 242);
            background-color: rgba(42, 43, 46, 194);
            border: 1px solid rgba(255, 255, 255, 64);
            border-radius: 7px;
            selection-background-color: rgba(134, 138, 154, 210);
        }

        QLineEdit:focus,
        QComboBox:focus,
        QSpinBox:focus {
            border: 1px solid rgba(220, 224, 238, 128);
            background-color: rgba(53, 54, 58, 218);
        }

        QPushButton {
            min-height: 28px;
            padding: 4px 16px;
            color: rgba(248, 248, 250, 240);
            background-color: rgba(55, 56, 60, 206);
            border: 1px solid rgba(255, 255, 255, 56);
            border-radius: 7px;
        }

        QPushButton:hover {
            background-color: rgba(72, 73, 78, 220);
            border-color: rgba(255, 255, 255, 88);
        }

        QPushButton:pressed {
            background-color: rgba(92, 94, 102, 226);
        }

        QPushButton:disabled,
        QLineEdit:disabled,
        QComboBox:disabled,
        QCheckBox:disabled,
        QListWidget:disabled {
            color: rgba(248, 248, 250, 92);
            background-color: rgba(255, 255, 255, 18);
        }

        QTableWidget,
        QListWidget,
        QFrame#queueGlass {
            color: rgba(248, 248, 250, 240);
            background-color: rgba(28, 29, 31, 172);
            alternate-background-color: rgba(255, 255, 255, 18);
            border: 1px solid rgba(255, 255, 255, 58);
            border-radius: 8px;
            gridline-color: rgba(255, 255, 255, 34);
            selection-background-color: rgba(124, 128, 144, 210);
            selection-color: rgb(255, 255, 255);
        }

        QHeaderView::section {
            min-height: 24px;
            padding: 4px 8px;
            color: rgba(248, 248, 250, 235);
            background-color: rgba(255, 255, 255, 40);
            border: 0;
            border-right: 1px solid rgba(255, 255, 255, 42);
            border-bottom: 1px solid rgba(255, 255, 255, 54);
        }

        QSplitter::handle {
            background-color: rgba(255, 255, 255, 42);
            border: 0;
        }

        QCheckBox {
            color: rgba(248, 248, 250, 230);
            spacing: 6px;
            background: transparent;
        }

        QCheckBox::indicator {
            width: 15px;
            height: 15px;
            border-radius: 4px;
            border: 1px solid rgba(255, 255, 255, 84);
            background-color: rgba(255, 255, 255, 34);
        }

        QCheckBox::indicator:checked {
            background-color: rgba(182, 186, 222, 232);
            border-color: rgba(228, 230, 246, 230);
        }

        QProgressBar {
            min-height: 16px;
            max-height: 18px;
            color: rgba(248, 248, 250, 235);
            background-color: rgba(255, 255, 255, 28);
            border: 1px solid rgba(255, 255, 255, 46);
            border-radius: 8px;
            text-align: center;
        }

        QProgressBar::chunk {
            border-radius: 8px;
            background-color: rgba(182, 186, 222, 220);
        }

        QWidget#queueRow {
            background-color: rgba(255, 255, 255, 20);
            border-radius: 6px;
        }

        QPushButton#queueActionButton {
            min-width: 24px;
            max-width: 24px;
            min-height: 24px;
            max-height: 24px;
            padding: 0;
            background-color: rgba(36, 37, 40, 210);
            border: 1px solid rgba(255, 255, 255, 60);
            border-radius: 6px;
        }

        QPushButton#queueActionButton:hover {
            background-color: rgba(77, 78, 84, 225);
            border-color: rgba(255, 255, 255, 105);
        }

        QWidget#queueRow QLabel {
            color: rgba(248, 248, 250, 235);
        }

        QScrollBar:vertical,
        QScrollBar:horizontal {
            background: transparent;
            border: 0;
            margin: 2px;
        }

        QScrollBar::handle:vertical,
        QScrollBar::handle:horizontal {
            background-color: rgba(210, 212, 218, 82);
            border-radius: 5px;
            min-height: 28px;
            min-width: 28px;
        }

        QScrollBar::add-line,
        QScrollBar::sub-line {
            width: 0;
            height: 0;
        }
        """
    )


def prepare_liquid_glass_window(window: QMainWindow) -> None:
    """Enable translucent composition for top-level windows when supported."""

    if sys.platform == "darwin" or sys.platform == "win32" or sys.platform.startswith("linux"):
        window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        window.setAutoFillBackground(False)
    if sys.platform == "darwin":
        window.setUnifiedTitleAndToolBarOnMac(True)
