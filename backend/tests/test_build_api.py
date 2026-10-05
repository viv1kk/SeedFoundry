"""M5: builds over HTTP (FR-B-1, FR-B-8, D-33, D-46, D-48, D-49): start, the intake lock and
its release, speed and skip (pacing only), Reset during a build, a finished build's events,
iteration 2 by API, and a server restart mid-build with the real engine."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from seedfoundry.engine.catalogue import PHASES
from seedfoundry.engine.clock import FakeClock
from seedfoundry.engine.runner import SLICE
from seedfoundry.main import create_app
from seedfoundry.state import Approval

CORE = ["person", "instrument_awareness", "environment", "music"]


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(auto=False)


@pytest.fixture
def api(var_dir, clock):
    with TestClient(create_app(var_dir, clock)) as client:
        yield client


def advance(client: TestClient, clock: FakeClock, seconds: float) -> None:
    client.portal.call(clock.advance, seconds)


def finish(client: TestClient, clock: FakeClock) -> None:
    """Skip to the end of the running build and wait until it is saved."""
    assert client.post("/api/demo/skip", json={"to": "build"}).status_code == 200
    advance(client, clock, SLICE)
    client.portal.call(client.app.state.engine.wait)


def state(client: TestClient) -> dict:
    return client.get("/api/state").json()


def events(client: TestClient, after: int = 0) -> list:
    return list(client.app.state.lab.log.after(after))


def start(client: TestClient, **body):
    return client.post("/api/builds", json=body or None)


def load(client: TestClient):
    assert client.post("/api/demo/sample", json={}).status_code == 201


# Start Build (FR-B-1)


def test_start_creates_a_build_for_the_current_iteration(api, clock):
    load(api)
    response = start(api)
    assert response.status_code == 201
    build = response.json()
    assert {k: build[k] for k in ("id", "iteration", "status", "seed_name", "phase")} == {
        "id": "b-1",
        "iteration": 1,
        "status": "running",
        "seed_name": "License Optimization",
        "phase": None,  # the record as created; Assay starts as the engine plays its first beats
    }
    assert [p["id"] for p in build["plan"]] == [p.id for p in PHASES]
    assert "log" not in build
    advance(api, clock, 0)
    snapshot = state(api)
    assert snapshot["builds"] == [{**build, "phase": "assay"}]
    assert snapshot["iteration"] == 1 and snapshot["next_build_id"] == 2
    started = next(e for e in events(api) if e.type == "build.started")
    assert started.data["build"]["id"] == "b-1" and started.data["replaces"] == []


def test_start_refuses_missing_or_blank_core_files(api):
    response = start(api)
    assert response.status_code == 409
    assert response.json()["detail"] == {
        "code": "core_files_missing",
        "message": "Start Build needs every initiation file. Missing: Identity.md, Tools_and_Skills.md, Environment.md, Value.md.",
        "missing": CORE,
    }
    for category in CORE:
        api.post("/api/intake/files", json={"name": f"{category}.md", "category": category, "content": "# x" if category != "music" else " \n\t"})
    response = start(api)
    assert response.json()["detail"]["missing"] == ["music"]  # whitespace only counts as missing (D-42 (a))
    assert state(api)["builds"] == []


def test_one_build_at_a_time(api, clock):
    load(api)
    start(api)
    response = start(api)
    assert response.status_code == 409 and response.json()["detail"]["code"] == "build_running"


# Intake lock (FR-B-8) and its release


def test_intake_is_read_only_while_a_build_runs_and_free_after(api, clock):
    load(api)
    file_id = state(api)["intake"]["files"][0]["id"]
    start(api)
    advance(api, clock, 5)
    refusals = [
        api.post("/api/intake/files", json={"name": "n.md", "category": "misc_context"}),
        api.patch(f"/api/intake/files/{file_id}", json={"content": "changed"}),
        api.delete(f"/api/intake/files/{file_id}"),
        api.post("/api/demo/sample", json={"replace": True}),
        api.post("/api/demo/clear"),
    ]
    assert [(r.status_code, r.json()["detail"]["code"]) for r in refusals] == [(409, "intake_locked")] * 5
    finish(api, clock)
    assert state(api)["builds"][0]["status"] == "completed"
    assert api.post("/api/intake/files", json={"name": "n.md", "category": "misc_context"}).status_code == 201


# Speed and skip (FR-DC-2, FR-DC-4, D-48)


def test_speed_is_kept_on_the_server_across_reset_and_emits_nothing(api):
    assert api.get("/api/demo/speed").json() == {"speed": 1}
    seq = state(api)["seq"]
    assert api.post("/api/demo/speed", json={"speed": 4}).json() == {"speed": 4}
    assert state(api)["seq"] == seq
    load(api)
    api.post("/api/demo/reset")
    assert api.get("/api/demo/speed").json() == {"speed": 4}
    assert api.post("/api/demo/speed", json={"speed": 3}).status_code == 422


def test_skip_needs_a_running_build(api):
    for to in ("phase", "build"):
        response = api.post("/api/demo/skip", json={"to": to})
        assert response.status_code == 409
        assert response.json()["detail"]["message"] == "No build is running, so there is nothing to skip."
    assert api.post("/api/demo/skip", json={"to": "nowhere"}).status_code == 422


def test_skip_phase_names_the_phase_it_skips(api, clock):
    load(api)
    start(api)
    advance(api, clock, 1)
    assert api.post("/api/demo/skip", json={"to": "phase"}).json() == {"skipping": "phase", "phase": "assay", "name": "Assay"}
    seq = state(api)["seq"]
    advance(api, clock, SLICE)
    assert [e.phase for e in events(api, seq) if e.type == "phase.completed"] == ["assay"]


def test_speed_and_skip_do_not_change_the_events(var_dir, tmp_path):
    def run(path, actions):
        clock = FakeClock(auto=False)
        with TestClient(create_app(path, clock)) as client:
            load(client)
            for action in actions:
                action(client, clock)
            start(client)
            advance(client, clock, 2)
            api_skip = client.post("/api/demo/skip", json={"to": "phase"})
            assert api_skip.status_code == 200
            advance(client, clock, 1)
            finish(client, clock)
            return [e.model_dump(mode="json", exclude={"wall_ts"}) for e in events(client)]

    slow = run(var_dir, [])
    fast = run(tmp_path / "fast", [lambda c, _: c.post("/api/demo/speed", json={"speed": 4})])
    assert slow == fast


# Reset during a build (D-46)


def test_reset_cancels_the_running_build_before_removing_it(api, clock):
    load(api)
    start(api)
    advance(api, clock, 6)
    assert api.post("/api/demo/reset").json() == {"files_removed": 4, "builds_removed": 1}
    after = state(api)
    assert after["builds"] == [] and after["intake"]["files"] == [] and after["iteration"] == 1
    assert not api.app.state.engine.running
    # A new build can start at once, and no beat of the old one lands after the reset.
    load(api)
    rebuilt = start(api).json()
    assert rebuilt["id"] == "b-2" and rebuilt["status"] == "running"
    advance(api, clock, 100)
    assert [e for e in events(api, after["seq"]) if e.build_id == "b-1"] == []


def test_the_record_carries_the_builds_simulated_length(api, clock):
    """The Build page reads progress as sim_t over this, at any speed (D-54)."""
    load(api)
    build = start(api).json()
    assert build["sim_seconds"] == 75.0
    finish(api, clock)
    record = state(api)["builds"][0]
    assert record["sim_seconds"] == 75.0
    last = api.get("/api/builds/b-1/events").json()["events"][-1]
    assert last["sim_t"] == record["sim_seconds"] == last["data"]["sim_seconds"]


# A build's events (D-49)


def test_a_finished_build_serves_its_kept_events(api, clock):
    load(api)
    start(api)
    advance(api, clock, 3)
    running = api.get("/api/builds/b-1/events").json()
    assert running["status"] == "running" and running["events"][0]["type"] == "build.started"
    finish(api, clock)
    body = api.get("/api/builds/b-1/events").json()
    streamed = [e.model_dump(mode="json") for e in events(api) if e.build_id == "b-1"]
    assert body["status"] == "completed" and body["events"] == streamed
    assert body["events"][-1]["type"] == "build.completed"
    assert "log" not in state(api)["builds"][0]
    assert api.get("/api/builds/b-9/events").status_code == 404


def test_a_new_build_replaces_the_iterations_earlier_one(api, clock):
    load(api)
    start(api)
    finish(api, clock)
    second = start(api).json()
    assert second["id"] == "b-2" and second["iteration"] == 1
    assert [b["id"] for b in state(api)["builds"]] == ["b-2"]
    started = [e for e in events(api) if e.type == "build.started"]
    assert [e.data["replaces"] for e in started] == [[], ["b-1"]]


# Iteration 2 starts with the rebuild (D-49, D-67; D-71: it started by API alone before M10)


def test_iteration_2_starts_by_api_after_a_completed_iteration_1(api, clock):
    load(api)
    assert start(api, iteration=2, feedback="Use bars.").json()["detail"]["code"] == "iteration_1_not_built"
    start(api)
    assert start(api, iteration=2, feedback="Use bars.").json()["detail"]["code"] == "build_running"
    finish(api, clock)
    assert start(api, iteration=2).json()["detail"]["code"] == "feedback_empty"
    second = start(api, iteration=2, feedback="Use bars.")
    assert second.status_code == 201 and second.json()["iteration"] == 2
    plan = second.json()["plan"][0]["steps"]
    assert [s["name"] for s in plan[:5]] == [
        "Route feedback to Ensemble files",
        "Update Identity.md",
        "Update Tools_and_Skills.md",
        "Update Environment.md",
        "Update Value.md",
    ]
    finish(api, clock)
    assert state(api)["iteration"] == 2
    assert [(b["id"], b["iteration"]) for b in state(api)["builds"]] == [("b-1", 1), ("b-2", 2)]
    assert start(api, iteration=1).json()["detail"]["code"] == "wrong_iteration"


def test_an_approved_seed_is_not_built_again(api, clock):
    load(api)
    start(api)
    finish(api, clock)
    api.app.state.lab.state.approval = Approval(iteration=1)
    response = start(api)
    assert response.status_code == 409 and response.json()["detail"]["code"] == "seed_approved"


# Restart mid-build (D-33), with the real engine and clock


def test_a_server_restart_mid_build_marks_it_interrupted(server):
    server.start()
    assert server.request("POST", "/api/demo/sample", {})[0] == 201
    seq = server.request("GET", "/api/state")[1]["seq"]
    status, build = server.request("POST", "/api/builds", {})
    assert status == 201
    with server.sse(f"/api/events?after={seq}") as stream:
        assert stream.frame()["event"] == "build.started"
        assert stream.frame()["event"] == "phase.started"
    server.kill()
    server.start()
    after = server.request("GET", "/api/state")[1]
    assert [(b["id"], b["status"]) for b in after["builds"]] == [("b-1", "interrupted")]
    assert server.request("POST", "/api/intake/files", {"name": "n.md", "category": "misc_context"})[0] == 201
    status, again = server.request("POST", "/api/builds", {})
    assert status == 201 and again["id"] == "b-2"
    assert [b["id"] for b in server.request("GET", "/api/state")[1]["builds"]] == ["b-2"]
