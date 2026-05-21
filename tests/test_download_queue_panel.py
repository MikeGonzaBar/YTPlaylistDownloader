from playlist_folder_downloader.gui.download_queue_panel import (
    QUEUE_BODY_MIN_HEIGHT,
    QUEUE_ROW_MIN_HEIGHT,
    DownloadQueuePanel,
)


def _tr(key: str) -> str:
    return key


def test_queue_panel_keeps_visible_body(qtbot) -> None:  # noqa: ANN001
    panel = DownloadQueuePanel(_tr)
    qtbot.addWidget(panel)

    assert panel.queue_scroll.minimumHeight() >= QUEUE_BODY_MIN_HEIGHT
    assert panel.queue_frame.minimumHeight() >= QUEUE_BODY_MIN_HEIGHT


def test_queue_row_keeps_height_when_hover_actions_change(qtbot) -> None:  # noqa: ANN001
    panel = DownloadQueuePanel(_tr)
    qtbot.addWidget(panel)

    panel.set_job("video-id", "Example video: queued", 0, "queued")
    row = panel._rows["video-id"]

    assert panel.empty_label is None
    assert row.minimumHeight() >= QUEUE_ROW_MIN_HEIGHT

    row._hovered = True
    row._sync_actions()

    assert row.minimumHeight() >= QUEUE_ROW_MIN_HEIGHT
    assert not row.remove_button.isHidden()
