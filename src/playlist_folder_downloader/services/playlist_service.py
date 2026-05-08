"""Playlist metadata loading via yt-dlp."""

from __future__ import annotations

from typing import Any

from playlist_folder_downloader.diagnostics import debug_print
from playlist_folder_downloader.models import PlaylistInfo, VideoInfo
from playlist_folder_downloader.services.js_runtime import build_js_runtime_options
from playlist_folder_downloader.services.yt_dlp_runner import (
    MetadataExtractionTimeout,
    extract_info_with_timeout,
)
from playlist_folder_downloader.utils.url_utils import (
    extract_playlist_id,
    extract_video_id,
    normalize_video_url,
)

UNAVAILABLE_TITLES = {"[deleted video]", "[private video]"}


def _entry_to_video(entry: dict[str, Any]) -> VideoInfo | None:
    video_id = str(entry.get("id") or "").strip()
    title = str(entry.get("title") or "").strip()
    if not video_id or title.lower() in UNAVAILABLE_TITLES:
        return None

    webpage_url = str(entry.get("webpage_url") or entry.get("url") or "").strip()
    if not webpage_url.startswith(("http://", "https://")):
        webpage_url = normalize_video_url(video_id)

    playlist_index = entry.get("playlist_index")
    if not isinstance(playlist_index, int):
        playlist_index = entry.get("playlist_autonumber") if isinstance(entry.get("playlist_autonumber"), int) else None

    duration = entry.get("duration")
    return VideoInfo(
        id=video_id,
        title=title or f"Video {video_id}",
        webpage_url=webpage_url,
        playlist_index=playlist_index,
        duration=duration if isinstance(duration, int) else None,
        channel=entry.get("channel") or entry.get("uploader"),
        thumbnail_url=entry.get("thumbnail"),
        availability_status=str(entry.get("availability") or "public"),
    )


def _video_info_to_single_collection(info: dict[str, Any], source_url: str) -> PlaylistInfo:
    video_id = str(info.get("id") or extract_video_id(source_url) or "").strip()
    if not video_id:
        raise ValueError("Could not find a video id in the supplied URL.")

    webpage_url = str(info.get("webpage_url") or normalize_video_url(video_id))
    title = str(info.get("title") or f"Video {video_id}").strip()
    video = VideoInfo(
        id=video_id,
        title=title,
        webpage_url=webpage_url,
        playlist_index=1,
        duration=info.get("duration") if isinstance(info.get("duration"), int) else None,
        channel=info.get("channel") or info.get("uploader"),
        thumbnail_url=info.get("thumbnail"),
        availability_status=str(info.get("availability") or "public"),
    )
    return PlaylistInfo(
        id=video_id,
        title=title or f"Video {video_id}",
        webpage_url=webpage_url,
        videos=[video],
    )


def load_playlist(url: str) -> PlaylistInfo:
    """Load playlist or single-video metadata without downloading media."""

    playlist_id = extract_playlist_id(url) or "playlist"
    video_id = extract_video_id(url)
    is_single_video = video_id is not None and extract_playlist_id(url) is None
    debug_print(
        "yt-dlp metadata extraction starting "
        f"(playlist_id={playlist_id if not is_single_video else 'none'}, "
        f"video_id={video_id or 'none'}, single_video={is_single_video})"
    )
    options = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": True,
        "ignoreerrors": True,
        "noplaylist": is_single_video,
        "socket_timeout": 20,
        "extractor_retries": 2,
    }
    options.update(build_js_runtime_options())
    try:
        info = extract_info_with_timeout(url, options, timeout_seconds=30)
    except MetadataExtractionTimeout:
        debug_print("metadata extraction timed out; retrying with forced IPv4")
        ipv4_options = {**options, "source_address": "0.0.0.0"}
        info = extract_info_with_timeout(url, ipv4_options, timeout_seconds=30)

    if not isinstance(info, dict):
        raise ValueError("Could not load playlist metadata.")

    if is_single_video:
        playlist = _video_info_to_single_collection(info, url)
        debug_print(f"yt-dlp metadata extraction finished (single video: {playlist.title})")
        return playlist

    entries = info.get("entries") or []
    videos: list[VideoInfo] = []
    warning_count = 0
    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            warning_count += 1
            continue
        video = _entry_to_video(entry)
        if video is None:
            warning_count += 1
            continue
        if not video.playlist_index or video.playlist_index < 1:
            video.playlist_index = position
        videos.append(video)

    title = str(info.get("title") or playlist_id or "Untitled Playlist").strip()
    webpage_url = str(info.get("webpage_url") or url)
    playlist = PlaylistInfo(
        id=str(info.get("id") or playlist_id),
        title=title or playlist_id,
        webpage_url=webpage_url,
        videos=videos,
        warning_count=warning_count,
    )
    debug_print(
        "yt-dlp metadata extraction finished "
        f"(title={playlist.title!r}, videos={len(videos)}, skipped={warning_count})"
    )
    return playlist
