"""Killable yt-dlp metadata extraction helpers."""

from __future__ import annotations

from multiprocessing import get_context
from multiprocessing.context import SpawnProcess
from multiprocessing.queues import Queue
from queue import Empty
from time import monotonic
from typing import Any

from playlist_folder_downloader.diagnostics import YtDlpDiagnosticLogger, debug_print


class MetadataExtractionError(RuntimeError):
    """Raised when yt-dlp metadata extraction fails."""


class MetadataExtractionTimeout(MetadataExtractionError):
    """Raised when yt-dlp metadata extraction exceeds the hard timeout."""


def _extract_info_child(url: str, options: dict[str, Any], queue: Queue) -> None:
    try:
        from yt_dlp import YoutubeDL

        child_options = dict(options)
        child_options["logger"] = YtDlpDiagnosticLogger()
        with YoutubeDL(child_options) as ydl:
            info = ydl.extract_info(url, download=False)
    except BaseException as exc:  # noqa: BLE001 - child process serializes all failures
        queue.put(
            {
                "ok": False,
                "error": str(exc),
                "error_type": exc.__class__.__name__,
            }
        )
        return

    queue.put({"ok": True, "info": info})


def _terminate_process(process: SpawnProcess) -> None:
    process.terminate()
    process.join(3)
    if process.is_alive():
        process.kill()
        process.join(3)


def _close_queue(queue: Queue) -> None:
    try:
        queue.close()
        queue.join_thread()
    except (OSError, ValueError):
        pass


def extract_info_with_timeout(
    url: str,
    options: dict[str, Any],
    *,
    timeout_seconds: int = 45,
) -> dict[str, Any]:
    """Run yt-dlp extraction in a child process so hangs can be killed."""

    ctx = get_context("spawn")
    queue: Queue = ctx.Queue(maxsize=1)
    process = ctx.Process(target=_extract_info_child, args=(url, options, queue), daemon=True)

    process_started = False
    try:
        debug_print(f"metadata child process starting (timeout={timeout_seconds}s)")
        process.start()
        process_started = True
        deadline = monotonic() + timeout_seconds
        payload: dict[str, Any] | None = None

        while monotonic() < deadline:
            try:
                payload = queue.get(timeout=0.1)
                break
            except Empty:
                if not process.is_alive():
                    break

        if payload is None:
            if process.is_alive():
                debug_print("metadata child process timed out; terminating")
                _terminate_process(process)
                raise MetadataExtractionTimeout(
                    "Timed out while loading metadata from YouTube. "
                    "This usually means YouTube or the network did not respond. "
                    "Try again, check the URL in a browser, or try a single video URL."
                )

            try:
                payload = queue.get_nowait()
            except Empty as exc:
                raise MetadataExtractionError(
                    f"yt-dlp metadata process exited without returning data (exit code {process.exitcode})."
                ) from exc

        process.join(3)
        if process.is_alive():
            debug_print("metadata child process returned data but did not exit; terminating")
            _terminate_process(process)

        if not payload.get("ok"):
            error = payload.get("error") or "yt-dlp could not load metadata."
            error_type = payload.get("error_type") or "yt-dlp"
            raise MetadataExtractionError(f"{error_type}: {error}")

        info = payload.get("info")
        if not isinstance(info, dict):
            raise MetadataExtractionError("yt-dlp did not return metadata.")

        debug_print("metadata child process returned data")
        return info
    finally:
        if process_started and process.is_alive():
            debug_print("metadata child process interrupted; terminating")
            _terminate_process(process)
        _close_queue(queue)
