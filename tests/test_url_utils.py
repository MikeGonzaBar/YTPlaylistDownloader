from playlist_folder_downloader.utils.url_utils import (
    extract_playlist_id,
    extract_video_id,
    is_probably_youtube_media_url,
    is_probably_youtube_playlist_url,
    normalize_video_url,
)


def test_playlist_url_parsing() -> None:
    url = "https://www.youtube.com/playlist?list=PL1234567890"

    assert extract_playlist_id(url) == "PL1234567890"
    assert is_probably_youtube_playlist_url(url)


def test_playlist_url_without_www() -> None:
    url = "https://youtube.com/playlist?list=PLABC"

    assert extract_playlist_id(url) == "PLABC"


def test_watch_url_with_list_parameter() -> None:
    url = "https://www.youtube.com/watch?v=VIDEO_ID&list=PLWATCH123"

    assert extract_playlist_id(url) == "PLWATCH123"
    assert extract_video_id(url) == "VIDEO_ID"


def test_invalid_url_handling() -> None:
    assert extract_playlist_id("") is None
    assert extract_playlist_id("not a url") is None
    assert extract_playlist_id("https://example.com/playlist?list=PL123") is None
    assert not is_probably_youtube_playlist_url("https://www.youtube.com/watch?v=VIDEO_ID")
    assert is_probably_youtube_media_url("https://www.youtube.com/watch?v=VIDEO_ID")


def test_single_video_url_parsing() -> None:
    assert extract_video_id("https://www.youtube.com/watch?v=VIDEO_ID") == "VIDEO_ID"
    assert extract_video_id("https://youtu.be/VIDEO_ID") == "VIDEO_ID"
    assert extract_video_id("https://www.youtube.com/shorts/VIDEO_ID") == "VIDEO_ID"
    assert extract_video_id("https://www.youtube.com/live/VIDEO_ID") == "VIDEO_ID"
    assert is_probably_youtube_media_url("https://youtu.be/VIDEO_ID")


def test_normalize_video_url() -> None:
    assert normalize_video_url("VIDEO_ID") == "https://www.youtube.com/watch?v=VIDEO_ID"
