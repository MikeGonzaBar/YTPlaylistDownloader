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
    """Painted translucent mesh background for the main app surface."""

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
        base.setColorAt(0.00, QColor(26, 17, 52, 235))
        base.setColorAt(0.24, QColor(10, 77, 126, 232))
        base.setColorAt(0.48, QColor(31, 73, 118, 232))
        base.setColorAt(0.70, QColor(143, 42, 78, 225))
        base.setColorAt(1.00, QColor(9, 41, 68, 235))
        painter.fillPath(path, base)

        overlays = [
            (QPointF(rect.width() * 0.18, rect.height() * 0.84), rect.width() * 0.55, QColor(10, 190, 220, 120)),
            (QPointF(rect.width() * 0.52, rect.height() * 0.58), rect.width() * 0.48, QColor(160, 43, 170, 115)),
            (QPointF(rect.width() * 0.82, rect.height() * 0.16), rect.width() * 0.50, QColor(249, 121, 43, 135)),
            (QPointF(rect.width() * 0.90, rect.height() * 0.68), rect.width() * 0.42, QColor(18, 134, 235, 125)),
        ]
        for center, radius, color in overlays:
            gradient = QRadialGradient(center, radius)
            gradient.setColorAt(0.0, color)
            gradient.setColorAt(0.55, QColor(color.red(), color.green(), color.blue(), 50))
            gradient.setColorAt(1.0, QColor(color.red(), color.green(), color.blue(), 0))
            painter.fillPath(path, gradient)

        sheen = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        sheen.setColorAt(0.0, QColor(255, 255, 255, 70))
        sheen.setColorAt(0.18, QColor(255, 255, 255, 20))
        sheen.setColorAt(1.0, QColor(255, 255, 255, 4))
        painter.fillPath(path, sheen)

        painter.setClipping(False)
        painter.setPen(QPen(QColor(255, 255, 255, 110), 1))
        painter.drawRoundedRect(rect, 18, 18)


def apply_liquid_glass_style(app: QApplication) -> None:
    """Apply a macOS-inspired translucent glass style.

    Qt Widgets does not expose Apple's private Liquid Glass material APIs, so this
    uses supported Qt styling to get the same product direction: translucent
    surfaces, bright highlights, soft borders, and compact native-feeling controls.
    """

    palette = app.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor(14, 22, 40, 220))
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255, 42))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(255, 255, 255, 32))
    palette.setColor(QPalette.ColorRole.Text, QColor(244, 248, 255))
    palette.setColor(QPalette.ColorRole.Button, QColor(255, 255, 255, 58))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(55, 169, 255, 190))
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
            color: rgba(255, 255, 255, 235);
            background: transparent;
        }

        QLineEdit,
        QComboBox,
        QSpinBox {
            min-height: 26px;
            padding: 3px 10px;
            color: rgba(255, 255, 255, 240);
            background-color: rgba(255, 255, 255, 42);
            border: 1px solid rgba(255, 255, 255, 108);
            border-radius: 10px;
            selection-background-color: rgba(55, 169, 255, 185);
        }

        QLineEdit:focus,
        QComboBox:focus,
        QSpinBox:focus {
            border: 1px solid rgba(135, 218, 255, 210);
            background-color: rgba(255, 255, 255, 62);
        }

        QPushButton {
            min-height: 28px;
            padding: 4px 16px;
            color: rgba(255, 255, 255, 238);
            background-color: rgba(255, 255, 255, 54);
            border: 1px solid rgba(255, 255, 255, 112);
            border-radius: 12px;
        }

        QPushButton:hover {
            background-color: rgba(255, 255, 255, 76);
            border-color: rgba(145, 221, 255, 175);
        }

        QPushButton:pressed {
            background-color: rgba(80, 176, 255, 132);
        }

        QPushButton:disabled,
        QLineEdit:disabled,
        QComboBox:disabled,
        QCheckBox:disabled,
        QListWidget:disabled {
            color: rgba(255, 255, 255, 100);
            background-color: rgba(255, 255, 255, 24);
        }

        QTableWidget,
        QListWidget,
        QFrame#queueGlass {
            color: rgba(255, 255, 255, 240);
            background-color: rgba(255, 255, 255, 34);
            alternate-background-color: rgba(255, 255, 255, 22);
            border: 1px solid rgba(255, 255, 255, 95);
            border-radius: 12px;
            gridline-color: rgba(255, 255, 255, 46);
            selection-background-color: rgba(28, 151, 255, 185);
            selection-color: rgb(255, 255, 255);
        }

        QHeaderView::section {
            min-height: 24px;
            padding: 4px 8px;
            color: rgba(255, 255, 255, 235);
            background-color: rgba(255, 255, 255, 32);
            border: 0;
            border-right: 1px solid rgba(255, 255, 255, 70);
            border-bottom: 1px solid rgba(255, 255, 255, 80);
        }

        QSplitter::handle {
            background-color: rgba(255, 255, 255, 65);
            border: 0;
        }

        QCheckBox {
            color: rgba(255, 255, 255, 230);
            spacing: 6px;
            background: transparent;
        }

        QCheckBox::indicator {
            width: 15px;
            height: 15px;
            border-radius: 5px;
            border: 1px solid rgba(255, 255, 255, 120);
            background-color: rgba(255, 255, 255, 54);
        }

        QCheckBox::indicator:checked {
            background-color: rgba(35, 160, 255, 220);
            border-color: rgba(150, 224, 255, 220);
        }

        QProgressBar {
            min-height: 8px;
            max-height: 10px;
            color: transparent;
            background-color: rgba(255, 255, 255, 45);
            border: 1px solid rgba(255, 255, 255, 72);
            border-radius: 5px;
            text-align: center;
        }

        QProgressBar::chunk {
            border-radius: 5px;
            background-color: rgba(120, 222, 255, 210);
        }

        QWidget#queueRow {
            background-color: rgba(255, 255, 255, 24);
            border-radius: 8px;
        }

        QWidget#queueRow QLabel {
            color: rgba(255, 255, 255, 235);
        }

        QScrollBar:vertical,
        QScrollBar:horizontal {
            background: transparent;
            border: 0;
            margin: 2px;
        }

        QScrollBar::handle:vertical,
        QScrollBar::handle:horizontal {
            background-color: rgba(68, 78, 92, 100);
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
    """Enable translucent composition for top-level windows when useful."""

    if sys.platform == "darwin":
        window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        window.setUnifiedTitleAndToolBarOnMac(True)
