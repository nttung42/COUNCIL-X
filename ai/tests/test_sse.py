"""Unit tests for the SSE plumbing (frame formatting + channel naming)."""

from __future__ import annotations

from shb.api.v1.endpoints.jobs import _sse, _terminal_frame
from shb.services.event_bus import channel


def test_channel_name():
    """The pub/sub channel is namespaced per job id."""
    assert channel("REQ-1") == "job-events:REQ-1"


def test_sse_frame_format():
    """An SSE frame carries the event type then a JSON data line."""
    frame = _sse("progress", {"progress": 55})
    assert frame == 'event: progress\ndata: {"progress": 55}\n\n'


def test_sse_frame_keeps_unicode():
    """Vietnamese stays readable (ensure_ascii=False)."""
    frame = _sse("status", {"msg": "Đang xử lý"})
    assert "Đang xử lý" in frame


def test_terminal_frame_done():
    """A completed job yields a 'done' frame carrying the result."""
    frame = _terminal_frame("completed", {"case_id": "REQ-1"}, None)
    assert frame.startswith("event: done")
    assert '"result"' in frame and "REQ-1" in frame


def test_terminal_frame_error():
    """A failed job yields an 'error' frame carrying the message."""
    frame = _terminal_frame("failed", None, "boom")
    assert frame.startswith("event: error")
    assert "boom" in frame
