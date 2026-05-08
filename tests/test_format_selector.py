import pytest

from playlist_folder_downloader.models import MediaFormat, VideoDownloadOptions
from playlist_folder_downloader.services.format_selector import (
    build_format_selector,
    quality_label_to_height,
)


def formats() -> list[MediaFormat]:
    return [
        MediaFormat("137", "mp4", "1080p", 1080, 1920, 30, "h264", "none", None, 4500, None, None, "1080p", True, False),
        MediaFormat("136", "mp4", "720p", 720, 1280, 30, "h264", "none", None, 2200, None, None, "720p", True, False),
        MediaFormat("140", "m4a", "audio", None, None, None, "none", "aac", 128, None, None, "en", "English", False, True),
        MediaFormat("141", "m4a", "audio", None, None, None, "none", "aac", 256, None, None, "es", "Spanish", False, True),
    ]


def test_video_audio_1080p_selector() -> None:
    options = VideoDownloadOptions(max_height=1080)

    assert build_format_selector(options, formats()) == "bv*[height<=1080]+ba/b[height<=1080]"


def test_video_only_selector() -> None:
    options = VideoDownloadOptions(include_video=True, include_audio=False, max_height=720)

    assert build_format_selector(options, formats()) == "bv*[height<=720]/bestvideo[height<=720]"


def test_audio_only_selector() -> None:
    options = VideoDownloadOptions(include_video=False, include_audio=True)

    assert build_format_selector(options, formats()) == "ba/bestaudio"


def test_custom_exact_format_ids() -> None:
    options = VideoDownloadOptions(
        selected_video_format_id="137",
        selected_audio_format_ids=["140"],
    )

    assert build_format_selector(options, formats()) == "137+140"


def test_multiple_audio_tracks_require_mkv() -> None:
    options = VideoDownloadOptions(
        selected_video_format_id="137",
        selected_audio_format_ids=["140", "141"],
        allow_multiple_audio_tracks=True,
        prefer_container="mp4",
    )

    assert build_format_selector(options, formats()) == "137+140+141"
    assert options.prefer_container == "mkv"


def test_embedded_subtitles_prefer_mkv() -> None:
    options = VideoDownloadOptions(subtitles_enabled=True, embed_subtitles=True, prefer_container="mp4")

    build_format_selector(options, formats())

    assert options.prefer_container == "mkv"


def test_invalid_no_video_no_audio_state() -> None:
    options = VideoDownloadOptions(include_video=False, include_audio=False)

    with pytest.raises(ValueError):
        build_format_selector(options, formats())


def test_quality_label_to_height() -> None:
    assert quality_label_to_height("2160p") == 2160
    assert quality_label_to_height("Best") is None
    assert quality_label_to_height("Audio only") is None
