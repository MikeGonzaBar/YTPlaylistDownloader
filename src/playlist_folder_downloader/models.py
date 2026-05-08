"""Typed data models for playlist metadata and download options."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class MediaFormat:
    format_id: str
    ext: str | None
    resolution: str | None
    height: int | None
    width: int | None
    fps: float | None
    vcodec: str | None
    acodec: str | None
    abr: float | None
    tbr: float | None
    filesize: int | None
    language: str | None
    format_note: str | None
    is_video: bool
    is_audio: bool


@dataclass(slots=True)
class SubtitleTrack:
    language: str
    ext: str
    url: str | None
    name: str | None
    source: str


@dataclass(slots=True)
class VideoInfo:
    id: str
    title: str
    webpage_url: str
    playlist_index: int | None
    duration: int | None
    channel: str | None
    thumbnail_url: str | None
    availability_status: str = "unknown"
    probed: bool = False
    formats: list[MediaFormat] = field(default_factory=list)
    subtitles: dict[str, list[SubtitleTrack]] = field(default_factory=dict)
    automatic_captions: dict[str, list[SubtitleTrack]] = field(default_factory=dict)


@dataclass(slots=True)
class PlaylistInfo:
    id: str
    title: str
    webpage_url: str
    videos: list[VideoInfo]
    warning_count: int = 0


@dataclass(slots=True)
class VideoDownloadOptions:
    include_video: bool = True
    include_audio: bool = True
    max_height: int | None = 1080
    selected_video_format_id: str | None = None
    selected_audio_format_ids: list[str] = field(default_factory=list)
    allow_multiple_audio_tracks: bool = False
    prefer_container: str = "mkv"
    subtitles_enabled: bool = False
    include_manual_subtitles: bool = True
    include_auto_subtitles: bool = False
    subtitle_languages: list[str] = field(default_factory=list)
    embed_subtitles: bool = True
    keep_subtitle_files: bool = False


@dataclass(slots=True)
class DownloadJob:
    video: VideoInfo
    options: VideoDownloadOptions
    output_dir: Path
    status: str
    progress: float
    message: str | None
