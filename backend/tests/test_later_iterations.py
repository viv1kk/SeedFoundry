"""Reject on any iteration (D-81) and the report's context footprint (D-82). Rejecting iteration 2
saves observer-feedback-iteration-2.md and starts iteration 3 from phase 1, which routes that feedback
into the four core files under `### Observer feedback (iteration 2)` and otherwise plays iteration 2's
outcome: the polished dashboard and no findings. The Seed's learned rules still come from iteration
1's findings, and its history runs through every iteration."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from seedfoundry import report
from seedfoundry.clients.llm import SIMULATED_CONTEXT_WINDOW
from seedfoundry.engine.clock import FakeClock
from seedfoundry.engine.script import BuildContext, script
from seedfoundry.intake.feedback import feedback_name
from seedfoundry.intake.routing import heading
from seedfoundry.main import create_app
from seedfoundry.sample import demo_feedback
from test_no_em_dash import em_dashes
from test_rebuild import AFTER, files_by_name, finish, two_iterations

# The core files after iteration 3: each versioned name has stepped twice (D-85).
THIRD = ("Identity.md", "Tools_and_Skills.md", "Environment_03.md", "Value_0003.md")


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(auto=False)


@pytest.fixture
def api(var_dir, clock):
    with TestClient(create_app(var_dir, clock)) as client:
        yield client


def reject(client: TestClient, iteration: int, feedback: str):
    """Reject `iteration` with `feedback`: Start Rebuild in the modal, which starts the next one."""
    return client.post("/api/builds", json={"iteration": iteration + 1, "feedback": feedback})


def three_iterations(client: TestClient, clock: FakeClock) -> None:
    two_iterations(client, clock)
    started = reject(client, 2, demo_feedback(2))
    assert started.status_code == 201 and started.json()["iteration"] == 3
    finish(client, clock)


def test_rejecting_iteration_2_starts_iteration_3_from_its_feedback(api, clock):
    three_iterations(api, clock)
    state = api.get("/api/state").json()
    assert state["iteration"] == 3
    assert [(b["id"], b["iteration"], b["status"]) for b in state["builds"]] == [("b-1", 1, "completed"), ("b-2", 2, "completed"), ("b-3", 3, "completed")]
    plan = state["builds"][2]["plan"]
    assert len(plan) == 11 and [s["name"] for s in plan[0]["steps"][:5]] == [
        "Route feedback to Ensemble files",
        "Update Identity.md",
        "Update Tools_and_Skills.md",
        "Update Environment.md",
        "Update Value.md",
    ]
    files = files_by_name(api)
    assert files[feedback_name(2)]["content"] == demo_feedback(2) and files[feedback_name(2)]["category"] == "misc_context"
    assert files[feedback_name(1)]["content"] == demo_feedback(1)  # the first feedback stays as it was
    # Each versioned name stepped once per iteration whose feedback changed the file (D-85).
    assert [n for n in files if n != feedback_name(1) and n != feedback_name(2)] == list(THIRD)
    for name in THIRD:  # the demo's refinements reach every core file, after the iteration 1 feedback
        content = files[name]["content"]
        assert f"### {heading(1)}" in content and f"### {heading(2)}" in content


def test_iteration_3_replays_iteration_2s_outcome(api, clock):
    three_iterations(api, clock)
    second, third = (api.get(f"/api/builds/{b}/report").json() for b in ("b-2", "b-3"))
    assert third["verdict"]["label"] == "Passed" and third["counts"]["findings"] == 0 and third["counts"]["advisories"] == 0
    assert third["counts"]["tests"] == second["counts"]["tests"] == 21
    changes = third["changes"]
    assert changes["prior_build_id"] == "b-2" and changes["findings"] == [] and changes["resolved"] == changes["open"] == 0
    assert changes["feedback"]["name"] == feedback_name(2) and changes["feedback"]["content"] == demo_feedback(2)
    assert {u["file"] for u in changes["updates"]} == set(AFTER.values())  # the names iteration 3 started from
    events = api.get("/api/builds/b-3/events").json()["events"]
    messages = [e["message"] for e in events]
    assert f"Read {feedback_name(2)}: 6 segments, {len(demo_feedback(2).encode())} bytes" in messages
    assert "Prior findings from iteration 2: 0" in messages
    assert "Learned rules for protection.md: 3 rules, one per finding class (Latency, Numeric, Visual)" in messages
    assert not [m for m in messages if em_dashes(m)]
    dashboard = "/api/dashboards/license-optimization"
    later, polished = (api.get(dashboard, params={"iteration": n}).json() for n in (3, 2))
    assert later.pop("iteration") == 3 and polished.pop("iteration") == 2 and later == polished


def test_iteration_rules_follow_the_current_iteration(api, clock):
    two_iterations(api, clock)
    assert reject(api, 1, "Again.").json()["detail"]["code"] == "wrong_iteration"
    assert api.post("/api/builds", json={"iteration": 4, "feedback": "Skip ahead."}).json()["detail"]["code"] == "wrong_iteration"
    assert reject(api, 2, "  ").json()["detail"] == {
        "code": "feedback_empty",
        "message": "Start Rebuild needs observer feedback. Write what iteration 3 should change first.",
    }
    assert reject(api, 2, "Sort the candidates by saving.").status_code == 201
    assert reject(api, 3, "More.").json()["detail"]["code"] == "build_running"
    finish(api, clock)
    refused = api.post("/api/seed/approve", json={"build_id": "b-2"}).json()["detail"]
    assert refused == {
        "code": "iteration_superseded",
        "message": "Iteration 3 was rebuilt from this build, so iteration 3 is the one to approve.",
    }
    assert api.post("/api/builds", json={"iteration": 5, "feedback": "Too far."}).json()["detail"]["code"] == "wrong_iteration"


def test_an_iteration_needs_the_one_before_it_completed(api, clock):
    two_iterations(api, clock)
    assert api.post("/api/builds", json={}).status_code == 201  # iteration 2 again, still running
    assert reject(api, 2, "Next.").json()["detail"]["code"] == "build_running"
    api.portal.call(api.app.state.engine.stop)
    api.post("/api/demo/reset")
    assert api.post("/api/demo/sample", json={}).status_code == 201
    detail = api.post("/api/builds", json={"iteration": 2, "feedback": "x"}).json()["detail"]
    assert detail == {"code": "iteration_1_not_built", "message": "Iteration 2 needs a completed iteration 1 build."}


def test_approving_iteration_3_gives_the_whole_history_and_the_learned_rules(api, clock):
    three_iterations(api, clock)
    page = api.post("/api/seed/approve", json={"build_id": "b-3"}).json()
    assert page["approval"]["iteration"] == 3 and page["known_issues"] == []
    shape = [(h["kind"], h.get("iteration", h.get("rejected")), h.get("approved")) for h in page["history"]]
    assert shape == [("iteration", 1, False), ("feedback", 1, None), ("iteration", 2, False), ("feedback", 2, None), ("iteration", 3, True)]
    feedback = page["history"][3]
    assert feedback["name"] == feedback_name(2) and feedback["routed"] == 5 and feedback["segments"] == 6 and feedback["files_updated"] == 4
    assert page["history"][4]["prior_findings"] == 0
    protection = next(f for f in page["files"] if f["name"] == "protection.md")
    assert protection["description"].endswith("It also holds the rules learned from iterations 1 and 2.")
    assert "One rule for each class of finding iteration 1 raised." in protection["content"]
    assert "Learned from iteration 1's N-1 (" in protection["content"]
    for f in page["files"]:
        assert "Known issues" not in f["content"] and not em_dashes(f["content"])
        assert api.get(f"/api/seed/files/{f['name']}").text == f["content"]


def test_the_demo_feedback_for_a_later_iteration_is_served_for_prefill(api):
    assert api.get("/api/demo/feedback", params={"rejected": 2}).json() == {"name": feedback_name(2), "content": demo_feedback(2)}
    assert api.get("/api/demo/feedback", params={"rejected": 5}).json()["name"] == "observer-feedback-iteration-5.md"
    assert demo_feedback(2) != demo_feedback(1) and not em_dashes(demo_feedback(2))


def test_iteration_3s_script_is_deterministic(api, clock):
    three_iterations(api, clock)
    state = api.app.state.lab.state
    given = state.build("b-2").files
    first, second = state.build("b-1"), state.build("b-2")
    files = [*given, *[f for f in state.intake.files if f.name == feedback_name(2)]]

    def play():
        return [(b.sim_t, b.events) for b in script(BuildContext("b-3", 3, files, prior=second, earlier=[first, second]))]

    assert play() == play()


# The context footprint (D-82)


def test_the_report_measures_the_seed_files_against_the_context_window(api, clock):
    three_iterations(api, clock)
    for build_id in ("b-1", "b-2", "b-3"):
        built = api.get(f"/api/builds/{build_id}/report").json()
        context = built["context"]
        events = api.get(f"/api/builds/{build_id}/events").json()["events"]
        manifest = next(e["data"]["manifest"] for e in events if e["step"] == "synth.manifest" and e["type"] == "log")
        assert context["window"] == SIMULATED_CONTEXT_WINDOW and context["budget"] == report.CONTEXT_BUDGET == 20
        assert [(layer["name"], layer["bytes"]) for layer in context["layers"]] == [(layer["name"], layer["bytes"]) for layer in manifest["layers"]]
        for layer in context["layers"]:
            assert layer["tokens"] == round(layer["bytes"] / 4)
            assert layer["share"] == round(layer["tokens"] / SIMULATED_CONTEXT_WINDOW * 100, 1)
        assert context["tokens"] == sum(layer["tokens"] for layer in context["layers"])
        assert context["within"] is True and 0 < context["share"] <= 20 and context["simulated"] is True


def test_a_seed_over_the_budget_reads_as_over():
    big = [{"name": n, "role": r, "bytes": 30_000} for n, r in (("core.md", "core"), ("adaptation.md", "adaptation"), ("protection.md", "protection"))]

    class Event:
        type, step, data = "log", "synth.manifest", {"manifest": {"layers": big}}

    context = report.context([Event()])  # type: ignore[list-item]
    assert context is not None and context["within"] is False and context["share"] == round(22_500 / SIMULATED_CONTEXT_WINDOW * 100, 1)
    assert report.context([]) is None
