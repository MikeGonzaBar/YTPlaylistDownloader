"""URL helpers for public YouTube playlist and video URLs."""

from __future__ import annotations

from urllib.parse import parse_qs, urlencode, urlparse

YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
}
YOUTUBE_SHORT_HOSTS = {"youtu.be"}


def _normalized_host(host: str | None) -> str:
    return (host or "").lower().removeprefix("www.")


def extract_playlist_id(url: str) -> str | None:
    """Extract the YouTube playlist id from supported playlist/watch URLs."""

    if not url or not url.strip():
        return None
    parsed = urlparse(url.strip())
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return None

    if not parsed.netloc:
        return None
    host = _normalized_host(parsed.netloc)
    if host not in {_normalized_host(item) for item in YOUTUBE_HOSTS}:
        return None

    query = parse_qs(parsed.query)
    playlist_ids = query.get("list")
    if not playlist_ids:
        return None

    playlist_id = playlist_ids[0].strip()
    return playlist_id or None


def extract_video_id(url: str) -> str | None:
    """Extract a public YouTube video id from supported watch/short URLs."""

    if not url or not url.strip():
        return None
    parsed = urlparse(url.strip())
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return None
    if not parsed.netloc:
        return None

    host = _normalized_host(parsed.netloc)
    if host in YOUTUBE_SHORT_HOSTS:
        video_id = parsed.path.strip("/").split("/", 1)[0]
        return video_id or None
    if host not in {_normalized_host(item) for item in YOUTUBE_HOSTS}:
        return None

    query = parse_qs(parsed.query)
    watch_id = (query.get("v") or [""])[0].strip()
    if watch_id:
        return watch_id

    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) >= 2 and path_parts[0] in {"shorts", "live", "embed"}:
        return path_parts[1] or None
    return None


def is_probably_youtube_playlist_url(url: str) -> bool:
    """Return true when a URL looks like a public YouTube playlist URL."""

    return extract_playlist_id(url) is not None


def is_probably_youtube_media_url(url: str) -> bool:
    """Return true when a URL looks like a public YouTube playlist or video URL."""

    return extract_playlist_id(url) is not None or extract_video_id(url) is not None


def normalize_video_url(video_id: str) -> str:
    """Build a canonical public YouTube watch URL from a video id."""

    return "https://www.youtube.com/watch?" + urlencode({"v": video_id})
