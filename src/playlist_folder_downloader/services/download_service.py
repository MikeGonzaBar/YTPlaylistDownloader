"""Authorized media download service built around yt-dlp."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from playlist_folder_downloader.diagnostics import YtDlpDiagnosticLogger, debug_print
from playlist_folder_downloader.models import DownloadJob
from playlist_folder_downloader.services.format_selector import build_format_selector
from playlist_folder_downloader.services.js_runtime import build_js_runtime_options
from playlist_folder_downloader.services.probe_service import probe_video
from playlist_folder_downloader.services.subtitle_selector import build_subtitle_options
from playlist_folder_downloader.utils.filenames import make_video_prefix, sanitize_filename


class DownloadCancelled(Exception):
    """Raised when a user cancels a running download."""


class DownloadFailed(Exception):
    """Raised when yt-dlp reports a readable download failure."""


def _merge_output_format(job: DownloadJob) -> str:
    options = job.options
    if options.allow_multiple_audio_tracks and len(options.selected_audio_format_ids) > 1:
        return "mkv"
    if options.subtitles_enabled and options.embed_subtitles:
        return "mkv"
    return options.prefer_container or "mkv"


def _outtmpl_literal(value: str) -> str:
    """Escape literal percent signs before inserting text into a yt-dlp outtmpl."""

    return value.replace("%", "%%")


def make_download_filename_template(job: DownloadJob) -> str:
    """Build the yt-dlp output template using the app's playlist row title."""

    prefix = make_video_prefix(job.video.playlist_index)
    title = sanitize_filename(job.video.title or "Untitled Video", max_length=180)
    return f"{prefix} - {_outtmpl_literal(title)} [%(id)s].%(ext)s"


def make_download_filename_preview(job: DownloadJob) -> str:
    """Return a user-facing filename preview before yt-dlp knows the final extension."""

    return (
        make_download_filename_template(job)
        .replace("%%", "%")
        .replace("%(id)s", job.video.id)
        .replace(".%(ext)s", ".[extension]")
    )


def download_video(
    job: DownloadJob,
    progress_callback: Callable[[dict[str, Any]], None],
    cancel_checker: Callable[[], bool],
) -> None:
    """Download one public/unrestricted video according to a DownloadJob."""

    from yt_dlp import YoutubeDL
    from yt_dlp.utils import DownloadError

    if cancel_checker():
        raise DownloadCancelled

    debug_print(f"download service preparing: {job.video.id}")
    original_video = job.video
    video = job.video if job.video.probed else probe_video(job.video.webpage_url)
    if not video.playlist_index:
        video.playlist_index = original_video.playlist_index
    if original_video.title:
        video.title = original_video.title
    job.video = video
    job.output_dir.mkdir(parents=True, exist_ok=True)

    def progress_hook(payload: dict[str, Any]) -> None:
        if cancel_checker():
            raise DownloadCancelled
        safe_payload = {
            key: value
            for key, value in payload.items()
            if key
            not in {
                "url",
                "fragment_url",
                "info_dict",
            }
        }
        progress_callback(safe_payload)

    ydl_options: dict[str, Any] = {
        "paths": {"home": str(Path(job.output_dir))},
        "outtmpl": {"default": make_download_filename_template(job)},
        "format": build_format_selector(job.options, video.formats),
        "merge_output_format": _merge_output_format(job),
        "progress_hooks": [progress_hook],
        "continuedl": True,
        "retries": 3,
        "fragment_retries": 3,
        "ignoreerrors": False,
        "restrictfilenames": False,
        "windowsfilenames": True,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "logger": YtDlpDiagnosticLogger(),
        "allow_multiple_audio_streams": bool(
            job.options.allow_multiple_audio_tracks and len(job.options.selected_audio_format_ids) > 1
        ),
    }
    ydl_options.update(build_subtitle_options(job.options))
    ydl_options.update(build_js_runtime_options())

    try:
        debug_print(f"yt-dlp download starting: {video.id}")
        with YoutubeDL(ydl_options) as ydl:
            ydl.download([video.webpage_url])
        debug_print(f"yt-dlp download finished: {video.id}")
    except DownloadCancelled:
        raise
    except DownloadError as exc:
        raise DownloadFailed(str(exc)) from exc
