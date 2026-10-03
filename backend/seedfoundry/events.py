"""Event log, SSE stream and snapshot-then-replay (seed-reuse-notes.md §2.2).

The client fetches GET /api/state, which carries the seq it is current as of,
then opens GET /api/events?after=<seq>. The stream replays every retained
event after that seq in order, then follows new ones. Each SSE frame's id is
the event's seq, so a browser that reconnects sends Last-Event-ID and gets an
exact replay.

The log lives in memory; the seq it continues from is saved with the state
(D-31). When the stream cannot replay exactly, because the events the client
asks for were lost in a server restart or the client's seq is ahead of the
server's, it sends one stream.resync frame and the client fetches a new
snapshot.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel

# The machine contract: build-simulation.md §3, plus the intake, resync and
# interrupted types added in M1 (D-31, D-33) and demo.reset in M4 (D-46).
BUILD_EVENT_TYPES = (
    "build.started",
    "phase.started",
    "step.started",
    "log",
    "llm.call",
    "api.call",
    "test.result",
    "gate.auto_resolved",
    "finding.raised",
    "step.completed",
    "phase.completed",
    "build.completed",
    "report.ready",
    "build.interrupted",
)
INTAKE_EVENT_TYPES = (
    "intake.file_created",
    "intake.file_updated",
    "intake.file_deleted",
)
# Demo controller (D-46): Reset to start. Load sample and Clear intake emit intake events.
DEMO_EVENT_TYPES = ("demo.reset",)
STREAM_EVENT_TYPES = ("stream.resync",)
EVENT_TYPES = BUILD_EVENT_TYPES + INTAKE_EVENT_TYPES + DEMO_EVENT_TYPES + STREAM_EVENT_TYPES

LEVELS = ("INFO", "LLM", "API", "TEST", "PASS", "WARN", "FAIL")

KEEPALIVE_SECONDS = 15.0


class Event(BaseModel):
    """One event, in the shape of build-simulation.md §3.

    sim_t is simulated seconds since build start and is null outside a build.
    wall_ts is the only wall-clock value and is ignored by determinism tests.
    """

    seq: int
    build_id: str | None = None
    iteration: int
    phase: str | None = None
    step: str | None = None
    type: str
    level: str = "INFO"
    code: str | None = None
    message: str
    data: dict[str, Any] = {}
    sim_t: float | None = None
    wall_ts: str


def wall_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class EventLog:
    """Events in seq order, contiguous from base + 1."""

    def __init__(self, base: int = 0) -> None:
        self.base = base
        self._events: list[Event] = []
        self._changed = asyncio.Event()

    @property
    def last_seq(self) -> int:
        return self.base + len(self._events)

    def extend(self, events: list[Event]) -> None:
        for event in events:
            if event.seq != self.last_seq + 1:
                raise ValueError(f"event seq {event.seq} does not follow {self.last_seq}")
            if event.type not in EVENT_TYPES:
                raise ValueError(f"unknown event type {event.type!r}")
            self._events.append(event)
        if events:
            changed, self._changed = self._changed, asyncio.Event()
            changed.set()

    def can_replay(self, after: int) -> bool:
        return self.base <= after <= self.last_seq

    def after(self, seq: int) -> list[Event]:
        """Retained events with a seq greater than the given one."""
        return self._events[max(seq - self.base, 0):]

    async def wait(self, timeout: float) -> bool:
        """Wait for the next append. False when the timeout passed first."""
        changed = self._changed
        try:
            await asyncio.wait_for(changed.wait(), timeout)
        except TimeoutError:
            return False
        return True


def sse_frame(event_type: str, seq: int, data: Any) -> str:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"id: {seq}\nevent: {event_type}\ndata: {payload}\n\n"


async def stream(log: EventLog, after: int, iteration: int, keepalive: float = KEEPALIVE_SECONDS) -> AsyncIterator[str]:
    """SSE text for one subscriber: replay after the given seq, then follow."""
    yield "retry: 1000\n\n"
    if not log.can_replay(after):
        seq = log.last_seq
        resync = Event(
            seq=seq,
            iteration=iteration,
            type="stream.resync",
            message="Event history is not available from that point. Fetch a new snapshot.",
            data={"requested_after": after, "seq": seq},
            wall_ts=wall_now(),
        )
        yield sse_frame(resync.type, seq, resync.model_dump(mode="json"))
        after = seq
    while True:
        events = log.after(after)
        for event in events:
            yield sse_frame(event.type, event.seq, event.model_dump(mode="json"))
        if events:
            after = events[-1].seq
            continue
        if not await log.wait(keepalive):
            yield ": keepalive\n\n"
