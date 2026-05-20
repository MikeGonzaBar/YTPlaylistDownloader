from __future__ import annotations

from queue import Empty
from typing import Any

import pytest

from playlist_folder_downloader.services import yt_dlp_runner


class FakeQueue:
    def __init__(self, payload: dict[str, Any] | None) -> None:
        self._payload = payload

    def get(self, timeout: float) -> dict[str, Any]:
        if self._payload is None:
            raise Empty
        payload = self._payload
        self._payload = None
        return payload

    def get_nowait(self) -> dict[str, Any]:
        return self.get(timeout=0)

    def close(self) -> None:
        pass

    def join_thread(self) -> None:
        pass


class FakeProcess:
    def __init__(self, alive_after_payload: bool) -> None:
        self.exitcode = None
        self.terminated = False
        self.killed = False
        self._alive = False
        self._alive_after_payload = alive_after_payload

    def start(self) -> None:
        self._alive = True

    def join(self, timeout: float) -> None:
        self._alive = self._alive_after_payload

    def is_alive(self) -> bool:
        return self._alive

    def terminate(self) -> None:
        self.terminated = True
        self._alive = False

    def kill(self) -> None:
        self.killed = True
        self._alive = False


class FakeContext:
    def __init__(self, payload: dict[str, Any] | None, *, alive_after_payload: bool = False) -> None:
        self.queue = FakeQueue(payload)
        self.process = FakeProcess(alive_after_payload)

    def Queue(self, maxsize: int) -> FakeQueue:  # noqa: N802 - mirrors multiprocessing API
        return self.queue

    def Process(self, **kwargs: object) -> FakeProcess:  # noqa: N802 - mirrors multiprocessing API
        return self.process


def test_extract_info_reads_payload_before_waiting_for_child_exit(monkeypatch) -> None:
    context = FakeContext({"ok": True, "info": {"id": "video-id"}}, alive_after_payload=True)
    monkeypatch.setattr(yt_dlp_runner, "get_context", lambda method: context)

    assert yt_dlp_runner.extract_info_with_timeout("url", {}, timeout_seconds=1) == {"id": "video-id"}
    assert context.process.terminated


def test_extract_info_timeout_terminates_child_without_payload(monkeypatch) -> None:
    context = FakeContext(None, alive_after_payload=True)
    monkeypatch.setattr(yt_dlp_runner, "get_context", lambda method: context)

    with pytest.raises(yt_dlp_runner.MetadataExtractionTimeout):
        yt_dlp_runner.extract_info_with_timeout("url", {}, timeout_seconds=0)

    assert context.process.terminated
