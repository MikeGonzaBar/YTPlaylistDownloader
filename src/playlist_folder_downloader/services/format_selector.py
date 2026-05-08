"""yt-dlp format selector construction."""

from __future__ import annotations

from playlist_folder_downloader.models import MediaFormat, VideoDownloadOptions

QUALITY_HEIGHTS: dict[str, int | None] = {
    "Best": None,
    "2160p": 2160,
    "1440p": 1440,
    "1080p": 1080,
    "720p": 720,
    "480p": 480,
    "Audio only": None,
    "Custom": None,
}


def quality_label_to_height(label: str) -> int | None:
    return QUALITY_HEIGHTS.get(label)


def _height_filter(max_height: int | None) -> str:
    return "" if max_height is None else f"[height<={max_height}]"


def _audio_ids(options: VideoDownloadOptions) -> list[str]:
    audio_ids = [item for item in options.selected_audio_format_ids if item]
    if len(audio_ids) > 1:
        options.prefer_container = "mkv"
        return audio_ids if options.allow_multiple_audio_tracks else audio_ids[:1]
    return audio_ids


def _ensure_format_id_exists(format_id: str | None, available_formats: list[MediaFormat]) -> str | None:
    if not format_id:
        return None
    if not available_formats:
        return format_id
    known_ids = {item.format_id for item in available_formats}
    return format_id if format_id in known_ids else None


def build_format_selector(
    options: VideoDownloadOptions,
    available_formats: list[MediaFormat],
) -> str:
    """Build a yt-dlp format selector for a video's selected options."""

    if not options.include_video and not options.include_audio:
        raise ValueError("At least one of video or audio must be enabled.")

    if options.subtitles_enabled and options.embed_subtitles:
        options.prefer_container = "mkv"

    selected_video = _ensure_format_id_exists(options.selected_video_format_id, available_formats)
    selected_audio = [
        item
        for item in _audio_ids(options)
        if _ensure_format_id_exists(item, available_formats) is not None
    ]

    height_filter = _height_filter(options.max_height)

    if options.include_video and options.include_audio:
        if selected_video and selected_audio:
            return "+".join([selected_video, *selected_audio])
        if options.max_height is None:
            return "bv*+ba/b"
        return f"bv*{height_filter}+ba/b{height_filter}"

    if options.include_video and not options.include_audio:
        if selected_video:
            return selected_video
        return f"bv*{height_filter}/bestvideo{height_filter}"

    selected_audio = _audio_ids(options)
    if selected_audio:
        return "+".join(selected_audio)
    return "ba/bestaudio"
