"""JSON translation manager using Qt's system locale detection."""

from __future__ import annotations

import json
from importlib.resources import files

from PySide6.QtCore import QLocale


class TranslationManager:
    """Small key/value translation manager with English fallback."""

    def __init__(self, language: str | None = None) -> None:
        self.language = self._resolve_language(language)
        self._english = self._load_language("en")
        self._strings = self._load_language(self.language)

    def _resolve_language(self, language: str | None) -> str:
        if language:
            return language.split("_", 1)[0].lower()
        system = QLocale.system().name()
        return (system.split("_", 1)[0] or "en").lower()

    def _load_language(self, language: str) -> dict[str, str]:
        try:
            resource = files("playlist_folder_downloader.i18n").joinpath(f"{language}.json")
            raw = resource.read_text(encoding="utf-8")
            data = json.loads(raw)
        except Exception:
            if language != "en":
                return self._load_language("en")
            return {}
        if not isinstance(data, dict):
            return {}
        return {str(key): str(value) for key, value in data.items()}

    def tr(self, key: str) -> str:
        return self._strings.get(key) or self._english.get(key) or key
