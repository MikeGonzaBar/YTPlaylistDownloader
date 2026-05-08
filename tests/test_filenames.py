from playlist_folder_downloader.models import DownloadJob, VideoDownloadOptions, VideoInfo
from playlist_folder_downloader.services.download_service import (
    make_download_filename_preview,
    make_download_filename_template,
)
from playlist_folder_downloader.utils.filenames import (
    make_playlist_folder_name,
    make_video_prefix,
    sanitize_filename,
)


def test_windows_illegal_characters() -> None:
    assert sanitize_filename('a<b>c:d"e/f\\g|h?i*j') == "a_b_c_d_e_f_g_h_i_j"


def test_reserved_names() -> None:
    assert sanitize_filename("CON") == "_CON"
    assert sanitize_filename("COM1.txt") == "_COM1.txt"


def test_long_names() -> None:
    value = sanitize_filename("x" * 300, max_length=50)

    assert len(value) == 50
    assert value == "x" * 50


def test_empty_names() -> None:
    assert sanitize_filename("") == "Untitled Video"
    assert make_playlist_folder_name("", "PL123") == "Untitled Playlist"


def test_playlist_folder_name_uses_playlist_title_only() -> None:
    assert make_playlist_folder_name("My Playlist", "PL123") == "My Playlist"


def test_trailing_dots_and_spaces() -> None:
    assert sanitize_filename(" name. ") == "name"


def test_video_prefix() -> None:
    assert make_video_prefix(None) == "000"
    assert make_video_prefix(7) == "007"
    assert make_video_prefix(1234) == "1234"


def test_download_filename_template_uses_video_title(tmp_path) -> None:
    video = VideoInfo(
        id="abc123",
        title='A <Great> 100% Video',
        webpage_url="https://www.youtube.com/watch?v=abc123",
        playlist_index=2,
        duration=None,
        channel=None,
        thumbnail_url=None,
    )
    job = DownloadJob(
        video=video,
        options=VideoDownloadOptions(),
        output_dir=tmp_path,
        status="queued",
        progress=0.0,
        message=None,
    )

    assert make_download_filename_template(job) == "002 - A _Great_ 100%% Video [%(id)s].%(ext)s"
    assert make_download_filename_preview(job) == "002 - A _Great_ 100% Video [abc123].[extension]"
