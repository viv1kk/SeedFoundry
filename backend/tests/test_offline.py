"""M12: the backend runs with the network disabled (NFR-2, AC-9, D-77). With the offline guard on,
every lookup or connection to a host other than loopback is refused and recorded; the whole demo
then runs in-process (Load sample, iteration 1, both dashboards and a drill, the reports, the
rebuild and iteration 2, Approve, every download, Reset) and the guard records nothing. A server
process gets the same guard in the rehearsal (frontend/scripts/rehearse.ts)."""

from __future__ import annotations

import socket

import pytest
from fastapi.testclient import TestClient

import offline
from seedfoundry.engine.clock import FakeClock
from seedfoundry.engine.runner import SLICE
from seedfoundry.main import create_app
from seedfoundry.sample import demo_feedback


@pytest.fixture
def guard():
    offline.attempts.clear()
    undo = offline.install()
    yield offline.attempts
    undo()


def test_the_guard_refuses_other_hosts_and_allows_loopback(guard):
    with pytest.raises(OSError, match="offline guard"):
        socket.getaddrinfo("example.com", 443)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe, pytest.raises(OSError, match="offline guard"):
        probe.connect(("203.0.113.7", 80))  # TEST-NET-3: refused before any packet leaves
    assert guard == ["lookup example.com", "connect 203.0.113.7"]
    assert socket.getaddrinfo("127.0.0.1", 80)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", 0))
        server.listen()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect(server.getsockname())
    assert len(guard) == 2


def test_the_whole_demo_runs_with_the_network_disabled(guard, var_dir):
    clock = FakeClock(auto=False)
    with TestClient(create_app(var_dir, clock)) as api:

        def finish() -> None:
            assert api.post("/api/demo/skip", json={"to": "build"}).status_code == 200
            api.portal.call(clock.advance, SLICE)
            api.portal.call(api.app.state.engine.wait)

        def ok(response, status: int = 200):
            assert response.status_code == status, response.text
            return response

        ok(api.get("/api/health"))
        ok(api.post("/api/demo/sample", json={}), 201)
        ok(api.post("/api/builds", json={}), 201)
        finish()
        ok(api.get("/api/builds/b-1/report"))
        ok(api.get("/api/builds/b-1/events"))
        for iteration in (1, 2):
            ok(api.get(f"/api/dashboards/license-optimization?iteration={iteration}"))
        ok(api.get("/api/dashboards/license-optimization?iteration=1&drill=microsoft"))
        ok(api.get("/api/dashboards/license-optimization/overlay"))
        ok(api.get("/api/datasets"))
        feedback = ok(api.get("/api/demo/feedback")).json()["content"]
        assert feedback == demo_feedback()
        ok(api.post("/api/builds", json={"iteration": 2, "feedback": feedback}), 201)
        finish()
        assert ok(api.get("/api/builds/b-2/report")).json()["verdict"]["label"] == "Passed"
        ok(api.post("/api/seed/approve", json={"build_id": "b-2"}), 201)
        for name in ("core.md", "adaptation.md", "protection.md"):
            ok(api.get(f"/api/seed/files/{name}"))
        assert ok(api.get("/api/seed/zip")).content[:2] == b"PK"
        ok(api.post("/api/demo/reset"))
    assert guard == []
