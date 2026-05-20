from __future__ import annotations

import io
import json
import sys

from playlist_folder_downloader import cli
from playlist_folder_downloader.models import VideoInfo


def test_probe_reads_minimal_video_payload_from_stdin(monkeypatch, capsys) -> None:
    payload = {
        "id": "abc123",
        "title": "Example",
        "webpage_url": "https://www.youtube.com/watch?v=abc123",
        "playlist_index": 2,
    }

    def fake_probe_video(url: str) -> VideoInfo:
        assert url == payload["webpage_url"]
        return VideoInfo(
            id="abc123",
            title="Fetched title",
            webpage_url=url,
            playlist_index=None,
            duration=12,
            channel="Channel",
            thumbnail_url=None,
            probed=True,
        )

    monkeypatch.setattr(cli, "probe_video", fake_probe_video)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))

    assert cli.main(["probe"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["event"] == "probed"
    assert output["video"]["id"] == "abc123"
    assert output["video"]["title"] == "Example"
    assert output["video"]["playlist_index"] == 2
