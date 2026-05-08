"""Application construction helpers."""

from __future__ import annotations

import sys
from importlib.resources import as_file, files

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from playlist_folder_downloader.diagnostics import debug_print
from playlist_folder_downloader.gui.main_window import MainWindow
from playlist_folder_downloader.gui.style import apply_liquid_glass_style
from playlist_folder_downloader.i18n.translation_manager import TranslationManager
from playlist_folder_downloader.logging_config import configure_logging
from playlist_folder_downloader.services.dependency_checker import check_dependencies
from playlist_folder_downloader.settings import load_settings


def _load_app_icon() -> QIcon | None:
    """Load the bundled app icon when package data is available."""

    try:
        icon_resource = files("playlist_folder_downloader").joinpath("assets/app_icon.png")
        with as_file(icon_resource) as icon_path:
            if icon_path.exists():
                return QIcon(str(icon_path))
    except (FileNotFoundError, ModuleNotFoundError, RuntimeError):
        return None
    return None


def create_app(argv: list[str] | None = None) -> tuple[QApplication, MainWindow]:
    """Create QApplication and the main window for testability."""

    debug_print("app create requested")
    app = QApplication.instance()
    if app is None:
        app = QApplication(argv or sys.argv)

    settings = load_settings()
    translations = TranslationManager(settings.language)
    configure_logging()
    dependencies = check_dependencies(settings.ffmpeg_path)
    apply_liquid_glass_style(app)
    window = MainWindow(settings, translations, dependencies)
    if icon := _load_app_icon():
        app.setWindowIcon(icon)
        window.setWindowIcon(icon)
    debug_print("app ready")
    return app, window
