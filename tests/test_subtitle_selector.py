from playlist_folder_downloader.models import VideoDownloadOptions
from playlist_folder_downloader.services.subtitle_selector import build_subtitle_options


def test_no_subtitles() -> None:
    assert build_subtitle_options(VideoDownloadOptions(subtitles_enabled=False)) == {}


def test_manual_subtitles() -> None:
    options = VideoDownloadOptions(
        subtitles_enabled=True,
        include_manual_subtitles=True,
        include_auto_subtitles=False,
        subtitle_languages=["es"],
    )

    result = build_subtitle_options(options)

    assert result["writesubtitles"] is True
    assert result["writeautomaticsub"] is False
    assert result["subtitleslangs"] == ["es"]
    assert result["subtitlesformat"] == "srt/best"


def test_auto_subtitles() -> None:
    options = VideoDownloadOptions(
        subtitles_enabled=True,
        include_manual_subtitles=False,
        include_auto_subtitles=True,
    )

    result = build_subtitle_options(options)

    assert result["writesubtitles"] is False
    assert result["writeautomaticsub"] is True


def test_language_fallback() -> None:
    options = VideoDownloadOptions(subtitles_enabled=True, subtitle_languages=[])

    assert build_subtitle_options(options)["subtitleslangs"] == ["en"]


def test_embed_subtitles() -> None:
    options = VideoDownloadOptions(
        subtitles_enabled=True,
        embed_subtitles=True,
        keep_subtitle_files=False,
    )

    result = build_subtitle_options(options)

    assert result["embedsubtitles"] is True
    assert "keepvideo" not in result
