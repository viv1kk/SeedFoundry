"""M1: event log and SSE, snapshot-then-replay (NFR-4, FR-B-7,
seed-reuse-notes.md §2.2). Replay order is checked on the stream generator
and over HTTP against a real server."""

from __future__ import annotations

import asyncio

import pytest

from seedfoundry.events import EVENT_TYPES, Event, EventLog, stream, wall_now

EVENT_FIELDS = ["seq", "build_id", "iteration", "phase", "step", "type", "level", "code", "message", "data", "sim_t", "wall_ts"]


def make(seq: int, type_: str = "log") -> Event:
    return Event(seq=seq, iteration=1, type=type_, message=f"event {seq}", wall_ts=wall_now())


def log_with(count: int, base: int = 0) -> EventLog:
    log = EventLog(base=base)
    log.extend([make(base + i + 1) for i in range(count)])
    return log


async def take(generator, count: int) -> list[str]:
    frames = []
    async for text in generator:
        if text.startswith(("retry:", ":")):
            continue
        frames.append(text)
        if len(frames) == count:
            break
    return frames


def ids(frames: list[str]) -> list[int]:
    return [int(frame.split("\n")[0].removeprefix("id: ")) for frame in frames]


# Log


def test_log_refuses_gaps_and_unknown_types():
    log = log_with(2)
    with pytest.raises(ValueError, match="does not follow"):
        log.extend([make(4)])
    with pytest.raises(ValueError, match="unknown event type"):
        log.extend([make(3, "nonsense")])


def test_log_after_returns_later_events_in_order():
    log = log_with(5)
    assert [e.seq for e in log.after(0)] == [1, 2, 3, 4, 5]
    assert [e.seq for e in log.after(3)] == [4, 5]
    assert log.after(5) == []


def test_log_after_restart_starts_from_base():
    log = log_with(2, base=10)
    assert log.last_seq == 12
    assert [e.seq for e in log.after(10)] == [11, 12]
    assert log.can_replay(10) and log.can_replay(12)
    assert not log.can_replay(9) and not log.can_replay(13)


def test_event_shape_matches_build_simulation_section_3():
    assert list(make(1).model_dump()) == EVENT_FIELDS


def test_intake_types_are_in_the_contract():
    assert {"intake.file_created", "intake.file_updated", "intake.file_deleted", "stream.resync"} <= set(EVENT_TYPES)


# Stream generator


def test_stream_replays_after_the_given_seq_in_order():
    frames = asyncio.run(take(stream(log_with(6), after=2, iteration=1), 4))
    assert ids(frames) == [3, 4, 5, 6]
    assert frames[0].startswith("id: 3\nevent: log\ndata: {")


def test_stream_follows_new_events_after_replay():
    async def scenario():
        log = log_with(2)
        subscriber = asyncio.ensure_future(take(stream(log, after=0, iteration=1), 4))
        await asyncio.sleep(0.05)
        log.extend([make(3)])
        await asyncio.sleep(0.05)
        log.extend([make(4)])
        return await asyncio.wait_for(subscriber, 2)

    assert ids(asyncio.run(scenario())) == [1, 2, 3, 4]


def test_stream_sends_keepalive_when_idle():
    async def scenario():
        generator = stream(EventLog(), after=0, iteration=1, keepalive=0.05)
        assert await anext(generator) == "retry: 1000\n\n"
        return await asyncio.wait_for(anext(generator), 2)

    assert asyncio.run(scenario()) == ": keepalive\n\n"


@pytest.mark.parametrize("after", [3, 20])
def test_stream_sends_resync_when_it_cannot_replay(after):
    # Base 5: events up to 5 were lost in a restart. 20 is ahead of the server.
    async def scenario():
        log = log_with(2, base=5)
        subscriber = asyncio.ensure_future(take(stream(log, after=after, iteration=1), 2))
        await asyncio.sleep(0.05)
        log.extend([make(8)])
        return await asyncio.wait_for(subscriber, 2)

    resync, following = asyncio.run(scenario())
    assert resync.startswith("id: 7\nevent: stream.resync\n")
    assert '"requested_after":%d' % after in resync
    assert ids([following]) == [8]


# Over HTTP, against a real server


def add_files(server, count: int) -> None:
    for i in range(count):
        status, _ = server.request("POST", "/api/intake/files", {"name": f"n{i}.md", "category": "misc_context"})
        assert status == 201


def test_sse_snapshot_then_replay_over_http(server):
    server.start()
    add_files(server, 3)
    _, snapshot = server.request("GET", "/api/state")
    assert snapshot["seq"] == 3
    with server.sse("/api/events?after=1") as sse:
        assert sse.headers["Content-Type"].startswith("text/event-stream")
        replayed = sse.frames(2)
        assert [f["id"] for f in replayed] == ["2", "3"]
        assert [f["event"] for f in replayed] == ["intake.file_created"] * 2
        assert replayed[0]["data"]["data"]["file"]["name"] == "n1.md"
        assert list(replayed[0]["data"]) == EVENT_FIELDS
        # Live: a change made while subscribed arrives next, in order.
        add_files(server, 1)
        live = sse.frame()
        assert (live["id"], live["data"]["seq"]) == ("4", 4)


def test_sse_reconnect_with_last_event_id_replays_exactly(server):
    server.start()
    add_files(server, 5)
    with server.sse("/api/events?after=0") as sse:
        first = sse.frames(2)
    assert [f["id"] for f in first] == ["1", "2"]
    # The browser reconnects to the same URL and sends the last id it saw.
    with server.sse("/api/events?after=0", last_event_id=2) as sse:
        assert [f["id"] for f in sse.frames(3)] == ["3", "4", "5"]


def test_sse_after_restart_resyncs_then_streams(server):
    server.start()
    add_files(server, 3)
    server.kill()
    server.start()
    # A client that had seen only seq 1 cannot get 2 and 3 back.
    with server.sse("/api/events", last_event_id=1) as sse:
        resync = sse.frame()
        assert (resync["event"], resync["id"]) == ("stream.resync", "3")
        add_files(server, 1)
        assert sse.frame()["id"] == "4"
    # A client current with the snapshot replays exactly, with no resync.
    with server.sse("/api/events?after=3") as sse:
        assert sse.frame()["id"] == "4"
