"""Event bus per-case trong bộ nhớ process — đẩy TraceEvent tới SSE subscriber.

Đủ dùng cho demo hackathon single-process (không cần Redis pub/sub). Mỗi case có
1 tập ``asyncio.Queue`` của các subscriber đang mở ``/api/cases/{id}/stream``.
Orchestrator gọi ``publish(case_id, event)`` mỗi bước; endpoint SSE ``subscribe``
để nhận.

Event dict shape (khớp contracts/appraisal-api.md mục 2):
    {step_name, component, active_tab, chat_message, t_offset_seconds, status}
``status`` in {"processing","completed","cancelled","error"}; giá trị terminal
báo hiệu endpoint đóng stream.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict

_subscribers: dict[str, set[asyncio.Queue]] = defaultdict(set)

TERMINAL_STATUSES = {"completed", "cancelled", "error"}


def subscribe(case_id: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _subscribers[case_id].add(q)
    return q


def unsubscribe(case_id: str, q: asyncio.Queue) -> None:
    subs = _subscribers.get(case_id)
    if subs and q in subs:
        subs.discard(q)
        if not subs:
            _subscribers.pop(case_id, None)


def publish(case_id: str, event: dict) -> None:
    """Đẩy event tới mọi subscriber của case (non-blocking)."""
    for q in list(_subscribers.get(case_id, ())):
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:  # pragma: no cover - queue không giới hạn
            pass
