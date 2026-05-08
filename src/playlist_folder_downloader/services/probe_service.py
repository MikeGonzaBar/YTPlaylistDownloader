"""Detailed video probing via yt-dlp."""

from __future__ import annotations

from typing import Any

from playlist_folder_downloader.diagnostics import debug_print
from playlist_folder_downloader.models import MediaFormat, SubtitleTrack, VideoInfo
from playlist_folder_downloader.services.js_runtime import build_js_runtime_options
from playlist_folder_downloader.services.yt_dlp_runner import (
    MetadataExtractionTimeout,
    extract_info_with_timeout,
)
from playlist_folder_downloader.utils.url_utils import normalize_video_url


def _number_or_none(value: Any) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    return None


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    return None


def _format_from_dict(raw_format: dict[str, Any]) -> MediaFormat:
    vcodec = raw_format.get("vcodec")
    acodec = raw_format.get("acodec")
    is_video = bool(vcodec and vcodec != "none")
    is_audio = bool(acodec and acodec != "none")
    filesize = raw_format.get("filesize") or raw_format.get("filesize_approx")
    return MediaFormat(
        format_id=str(raw_format.get("format_id") or ""),
        ext=raw_format.get("ext"),
        resolution=raw_format.get("resolution"),
        height=_int_or_none(raw_format.get("height")),
        width=_int_or_none(raw_format.get("width")),
        fps=_number_or_none(raw_format.get("fps")),
        vcodec=vcodec,
        acodec=acodec,
        abr=_number_or_none(raw_format.get("abr")),
        tbr=_number_or_none(raw_format.get("tbr")),
        filesize=filesize if isinstance(filesize, int) else None,
        language=raw_format.get("language"),
        format_note=raw_format.get("format_note"),
        is_video=is_video,
        is_audio=is_audio,
    )


def _subtitle_tracks(raw_subtitles: dict[str, Any], source: str) -> dict[str, list[SubtitleTrack]]:
    tracks: dict[str, list[SubtitleTrack]] = {}
    for language, entries in raw_subtitles.items():
        if not isinstance(entries, list):
            continue
        language_tracks: list[SubtitleTrack] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            ext = str(entry.get("ext") or "unknown")
            language_tracks.append(
                SubtitleTrack(
                    language=str(language),
                    ext=ext,
                    url=entry.get("url"),
                    name=entry.get("name"),
                    source=source,
                )
            )
        if language_tracks:
            tracks[str(language)] = language_tracks
    return tracks


def video_info_from_yt_dlp(info: dict[str, Any]) -> VideoInfo:
    video_id = str(info.get("id") or "").strip()
    if not video_id:
        raise ValueError("Video metadata did not include an id.")

    webpage_url = str(info.get("webpage_url") or "").strip()
    if not webpage_url:
        webpage_url = normalize_video_url(video_id)

    formats = [
        _format_from_dict(item)
        for item in info.get("formats", [])
        if isinstance(item, dict) and item.get("format_id")
    ]

    return VideoInfo(
        id=video_id,
        title=str(info.get("title") or f"Video {video_id}"),
        webpage_url=webpage_url,
        playlist_index=info.get("playlist_index") if isinstance(info.get("playlist_index"), int) else None,
        duration=info.get("duration") if isinstance(info.get("duration"), int) else None,
        channel=info.get("channel") or info.get("uploader"),
        thumbnail_url=info.get("thumbnail"),
        availability_status=str(info.get("availability") or "public"),
        probed=True,
        formats=formats,
        subtitles=_subtitle_tracks(info.get("subtitles") or {}, "manual"),
        automatic_captions=_subtitle_tracks(info.get("automatic_captions") or {}, "automatic"),
    )


def probe_video(video_url: str) -> VideoInfo:
    """Probe one public/unrestricted video without downloading media."""

    debug_print("yt-dlp video probe starting")
    options = {
        "quiet": True,
        "skip_download": True,
        "ignoreerrors": False,
        "noplaylist": True,
        "socket_timeout": 20,
        "extractor_retries": 2,
    }
    options.update(build_js_runtime_options())
    try:
        info = extract_info_with_timeout(video_url, options, timeout_seconds=30)
    except MetadataExtractionTimeout:
        debug_print("video probe timed out; retrying with forced IPv4")
        ipv4_options = {**options, "source_address": "0.0.0.0"}
        info = extract_info_with_timeout(video_url, ipv4_options, timeout_seconds=30)

    if not isinstance(info, dict):
        raise ValueError("Could not probe video metadata.")
    video = video_info_from_yt_dlp(info)
    debug_print(
        "yt-dlp video probe finished "
        f"(video_id={video.id}, formats={len(video.formats)}, "
        f"manual_subtitle_langs={len(video.subtitles)}, auto_subtitle_langs={len(video.automatic_captions)})"
    )
    return video
