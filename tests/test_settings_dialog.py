from playlist_folder_downloader.gui.settings_dialog import SettingsDialog
from playlist_folder_downloader.settings import AppSettings


def _tr(key: str) -> str:
    return key


def test_settings_dialog_uses_detected_ffmpeg_path(qtbot) -> None:  # noqa: ANN001
    dialog = SettingsDialog(AppSettings(ffmpeg_path=None), _tr, "/usr/bin/ffmpeg")
    qtbot.addWidget(dialog)

    assert dialog.ffmpeg_path.text() == "/usr/bin/ffmpeg"


def test_settings_dialog_keeps_saved_ffmpeg_override(qtbot) -> None:  # noqa: ANN001
    dialog = SettingsDialog(AppSettings(ffmpeg_path="/opt/bin/ffmpeg"), _tr, "/usr/bin/ffmpeg")
    qtbot.addWidget(dialog)

    assert dialog.ffmpeg_path.text() == "/opt/bin/ffmpeg"
