"""yt-dlp subtitle option construction."""

from __future__ import annotations

from typing import Any

from playlist_folder_downloader.models import VideoDownloadOptions


def build_subtitle_options(options: VideoDownloadOptions) -> dict[str, Any]:
    """Build subtitle-related yt-dlp options."""

    if not options.subtitles_enabled:
        return {}

    languages = [item.strip() for item in options.subtitle_languages if item.strip()] or ["en"]
    result: dict[str, Any] = {
        "writesubtitles": bool(options.include_manual_subtitles),
        "writeautomaticsub": bool(options.include_auto_subtitles),
        "subtitleslangs": languages,
        "subtitlesformat": "srt/best",
    }
    if options.embed_subtitles:
        result["embedsubtitles"] = True
    if options.keep_subtitle_files and options.embed_subtitles:
        result["keepvideo"] = True
    return result
