"""JSON-lines backend bridge for native frontends."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from playlist_folder_downloader.models import (
    DownloadJob,
    MediaFormat,
    SubtitleTrack,
    VideoDownloadOptions,
    VideoInfo,
)
from playlist_folder_downloader.services.download_service import (
    DownloadCancelled,
    DownloadFailed,
    download_video,
    make_download_filename_preview,
)
from playlist_folder_downloader.services.playlist_service import load_playlist
from playlist_folder_downloader.services.probe_service import probe_video
from playlist_folder_downloader.utils.filenames import make_playlist_folder_name


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def _emit_failure(command: str, exc: BaseException) -> int:
    _emit(
        {
            "event": "failed",
            "command": command,
            "error": str(exc) or exc.__class__.__name__,
            "error_type": exc.__class__.__name__,
        }
    )
    return 1


def _video_to_dict(video: VideoInfo) -> dict[str, Any]:
    data = asdict(video)
    data["formats"] = [asdict(item) if isinstance(item, MediaFormat) else item for item in video.formats]
    return data


def _media_format_from_dict(data: dict[str, Any]) -> MediaFormat:
    vcodec = data.get("vcodec")
    acodec = data.get("acodec")
    return MediaFormat(
        format_id=str(data.get("format_id") or ""),
        ext=data.get("ext"),
        resolution=data.get("resolution"),
        height=data.get("height") if isinstance(data.get("height"), int) else None,
        width=data.get("width") if isinstance(data.get("width"), int) else None,
        fps=float(data["fps"]) if isinstance(data.get("fps"), int | float) else None,
        vcodec=vcodec,
        acodec=acodec,
        abr=float(data["abr"]) if isinstance(data.get("abr"), int | float) else None,
        tbr=float(data["tbr"]) if isinstance(data.get("tbr"), int | float) else None,
        filesize=data.get("filesize") if isinstance(data.get("filesize"), int) else None,
        language=data.get("language"),
        format_note=data.get("format_note"),
        is_video=bool(data.get("is_video")),
        is_audio=bool(data.get("is_audio")),
    )


def _subtitle_tracks_from_dict(raw_tracks: Any, fallback_source: str) -> dict[str, list[SubtitleTrack]]:
    if not isinstance(raw_tracks, dict):
        return {}

    tracks: dict[str, list[SubtitleTrack]] = {}
    for language, entries in raw_tracks.items():
        if not isinstance(entries, list):
            continue

        language_tracks = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            language_tracks.append(
                SubtitleTrack(
                    language=str(entry.get("language") or language),
                    ext=str(entry.get("ext") or "unknown"),
                    url=entry.get("url"),
                    name=entry.get("name"),
                    source=str(entry.get("source") or fallback_source),
                )
            )
        if language_tracks:
            tracks[str(language)] = language_tracks
    return tracks


def _video_from_dict(data: dict[str, Any]) -> VideoInfo:
    formats = [
        _media_format_from_dict(item)
        for item in data.get("formats", [])
        if isinstance(item, dict)
    ]
    video_data = {
        "id": data["id"],
        "title": data.get("title") or f"Video {data['id']}",
        "webpage_url": data.get("webpage_url") or "",
        "playlist_index": data.get("playlist_index"),
        "duration": data.get("duration"),
        "channel": data.get("channel"),
        "thumbnail_url": data.get("thumbnail_url"),
        "availability_status": data.get("availability_status", "unknown"),
        "probed": data.get("probed", False),
        "formats": formats,
        "subtitles": _subtitle_tracks_from_dict(data.get("subtitles"), "manual"),
        "automatic_captions": _subtitle_tracks_from_dict(data.get("automatic_captions"), "automatic"),
    }
    return VideoInfo(**video_data)


def _options_from_dict(data: dict[str, Any]) -> VideoDownloadOptions:
    allowed = VideoDownloadOptions().__dataclass_fields__.keys()
    values = {key: data[key] for key in allowed if key in data}
    return VideoDownloadOptions(**values)


def command_load(url: str) -> int:
    try:
        playlist = load_playlist(url)
    except Exception as exc:  # noqa: BLE001 - CLI bridge must serialize backend failures
        return _emit_failure("load", exc)

    _emit(
        {
            "event": "loaded",
            "playlist": {
                "id": playlist.id,
                "title": playlist.title,
                "webpage_url": playlist.webpage_url,
                "warning_count": playlist.warning_count,
                "videos": [_video_to_dict(video) for video in playlist.videos],
            },
        }
    )
    return 0


def command_probe(video_json: str) -> int:
    try:
        video = _video_from_dict(json.loads(video_json))
        probed = probe_video(video.webpage_url)
    except Exception as exc:  # noqa: BLE001 - CLI bridge must serialize backend failures
        return _emit_failure("probe", exc)

    if not probed.playlist_index:
        probed.playlist_index = video.playlist_index
    if video.title:
        probed.title = video.title
    _emit({"event": "probed", "video": _video_to_dict(probed)})
    return 0


def command_download() -> int:
    payload = json.loads(sys.stdin.read())
    playlist = payload.get("playlist", {})
    playlist_title = playlist.get("title") or "Untitled Playlist"
    playlist_id = playlist.get("id") or ""
    output_root = Path(payload["download_root"]).expanduser()
    output_dir = output_root / make_playlist_folder_name(playlist_title, playlist_id)

    for raw_job in payload.get("jobs", []):
        try:
            video = _video_from_dict(raw_job["video"])
            options = _options_from_dict(raw_job.get("options", {}))
        except Exception as exc:  # noqa: BLE001 - bridge must serialize malformed job failures
            raw_video = raw_job.get("video", {}) if isinstance(raw_job, dict) else {}
            video_id = raw_video.get("id") if isinstance(raw_video, dict) else None
            title = raw_video.get("title") if isinstance(raw_video, dict) else None
            _emit(
                {
                    "event": "failed",
                    "video_id": video_id or "unknown",
                    "title": title or "Unknown video",
                    "error": str(exc),
                }
            )
            continue

        job = DownloadJob(
            video=video,
            options=options,
            output_dir=output_dir,
            status="queued",
            progress=0.0,
            message=None,
        )
        preview = make_download_filename_preview(job)
        _emit({"event": "started", "video_id": video.id, "title": video.title, "filename": preview})
        final_filename = preview
        video_id = video.id
        video_title = video.title

        def progress(
            payload: dict[str, Any],
            video_id: str = video_id,
            video_title: str = video_title,
        ) -> None:
            nonlocal final_filename
            total = payload.get("total_bytes") or payload.get("total_bytes_estimate") or 0
            downloaded = payload.get("downloaded_bytes") or 0
            percent = (float(downloaded) / float(total) * 100.0) if total else 0.0
            filename = payload.get("filename") or payload.get("tmpfilename")
            if filename:
                final_filename = Path(str(filename)).name
            if payload.get("status") == "finished":
                percent = 100.0
            _emit(
                {
                    "event": "progress",
                    "video_id": video_id,
                    "title": video_title,
                    "percent": percent,
                    "speed": payload.get("_speed_str") or "",
                    "eta": payload.get("_eta_str") or "",
                }
            )

        try:
            download_video(job, progress, lambda: False)
        except DownloadCancelled:
            _emit({"event": "canceled", "video_id": video.id, "title": video.title})
        except DownloadFailed as exc:
            _emit({"event": "failed", "video_id": video.id, "title": video.title, "error": str(exc)})
        except Exception as exc:  # noqa: BLE001 - bridge must serialize unexpected failures
            _emit({"event": "failed", "video_id": video.id, "title": video.title, "error": str(exc)})
        else:
            _emit(
                {
                    "event": "finished",
                    "video_id": video.id,
                    "title": video.title,
                    "filename": final_filename,
                }
            )

    _emit({"event": "all_finished", "output_dir": str(output_dir)})
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Playlist Folder Downloader backend bridge")
    subparsers = parser.add_subparsers(dest="command", required=True)

    load_parser = subparsers.add_parser("load")
    load_parser.add_argument("url")

    probe_parser = subparsers.add_parser("probe")
    probe_parser.add_argument("video_json", nargs="?")

    subparsers.add_parser("download")

    args = parser.parse_args(argv)
    if args.command == "load":
        return command_load(args.url)
    if args.command == "probe":
        return command_probe(args.video_json if args.video_json is not None else sys.stdin.read())
    if args.command == "download":
        return command_download()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
