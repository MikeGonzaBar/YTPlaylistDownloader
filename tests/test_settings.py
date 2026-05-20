from pathlib import Path

from playlist_folder_downloader.settings import AppSettings, load_settings, save_settings


def test_missing_settings_file(tmp_path: Path) -> None:
    settings = load_settings(tmp_path / "missing.json")

    assert isinstance(settings, AppSettings)
    assert settings.max_concurrent_downloads == 1
    assert settings.default_quality == "Best"


def test_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{not json", encoding="utf-8")

    settings = load_settings(path)

    assert settings.default_subtitle_languages == ["en"]


def test_save_load_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    original = AppSettings(
        download_root=str(tmp_path / "downloads"),
        language="es",
        max_concurrent_downloads=3,
        ffmpeg_path="/usr/bin/ffmpeg",
        default_quality="720p",
        default_include_audio=False,
        default_include_video=True,
        default_subtitles_enabled=True,
        default_subtitle_languages=["en", "es"],
    )

    save_settings(original, path)
    loaded = load_settings(path)

    assert loaded == original
