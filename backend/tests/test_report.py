"""M9: the build report (FR-R-1, FR-R-2, FR-R-4, D-64), assembled from a finished build's kept
events: header and verdict, grouped findings, the tests table, the gates and simulated usage, for
both iterations; report.ready; deterministic (NFR-1) and the same after a restart; the frontend's
fixtures."""

from __future__ import annotations

import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from report_fixtures import NAMES, FIXTURE_DIR, render, sample_builds
from seedfoundry import demo, report
from seedfoundry.engine.catalogue import PHASES, TEST_NAMES
from seedfoundry.engine.clock import FakeClock
from seedfoundry.engine.runner import BuildEngine
from seedfoundry.main import create_app
from seedfoundry.state import StateManager
from test_no_em_dash import em_dashes

CATALOGUE = ["N-1", "N-2", "N-3", "N-4", "N-5", "V-1", "V-2", "V-3", "V-4", "V-5", "V-6", "V-7", "V-8", "L-1"]


@pytest.fixture(scope="module")
def builds():
    return sample_builds()


@pytest.fixture(scope="module")
def reports(builds):
    return report.assemble(builds[0]), report.assemble(builds[1])


def test_the_header_gives_verdict_iteration_duration_and_counts(reports):
    one, two = reports
    assert (one["iteration"], one["seed_name"], one["duration"]) == (1, "License Optimization", 75.0)
    assert one["verdict"] == {"id": "findings", "label": "Completed with findings", "tone": "warning"}
    assert one["counts"] == {
        "phases": 11,
        "phases_with_findings": 2,
        "tests": 21,
        "pass": 15,
        "warn": 5,
        "fail": 1,
        "not_run": 0,
        "findings": 14,
        "advisories": 0,
        "gates": 3,
    }
    assert two["verdict"] == {"id": "passed", "label": "Passed", "tone": "positive"}
    assert {k: two["counts"][k] for k in ("tests", "pass", "warn", "fail", "findings", "phases_with_findings")} == {
        "tests": 21,
        "pass": 21,
        "warn": 0,
        "fail": 0,
        "findings": 0,
        "phases_with_findings": 0,
    }


def test_findings_are_grouped_numeric_visual_latency_boundary(reports):
    one, two = reports
    assert [(g["category"], [f["id"] for f in g["findings"]]) for g in one["groups"]] == [
        ("Numeric", CATALOGUE[:5]),
        ("Visual", CATALOGUE[5:13]),
        ("Latency", ["L-1"]),
        ("Boundary", []),
    ]
    for group in one["groups"]:
        for f in group["findings"]:
            assert {"id", "panel", "panels", "panel_titles", "expected", "shown", "severity", "phase", "message"} <= set(f)
    assert [g["findings"] for g in two["groups"]] == [[], [], [], []]


def test_the_tests_table_lists_every_test_with_its_phase_and_result(builds, reports):
    one, _ = reports
    assert [t["id"] for t in one["tests"]] == list(TEST_NAMES)
    by_phase = {t: p.id for p in PHASES for t, _ in p.tests}
    assert all(t["phase"] == by_phase[t["id"]] and t["name"] == TEST_NAMES[t["id"]] for t in one["tests"])
    results = {e.code: e.data["status"] for e in builds[0].log if e.type == "test.result"}
    assert {t["id"]: t["status"] for t in one["tests"]} == results
    assert [p["result"] for p in one["phases"]] == ["passed"] * 8 + ["findings", "findings", "passed"]
    assert one["phases"][8]["findings"] == ["L-1"]


def test_gates_say_how_each_was_resolved(reports):
    gates = reports[0]["gates"]
    assert [(g["id"], g["kind"], g["basis"]["file"], g["basis"]["section"]) for g in gates] == [
        ("servicenow-incident-api", "credentials", "environment.md", "Protection Layer"),
        ("solution-approval", "approval", "music.md", "Decision Logic"),
        ("close-seeding", "confirmation", "environment.md", "Protection Layer"),
    ]
    assert gates[1]["resolution"] == "approve License Optimization at potential PARTIAL"


def test_simulated_usage_is_counted_from_the_events(builds, reports):
    log = builds[0].log
    llm = [e for e in log if e.type == "llm.call"]
    api = [e for e in log if e.type == "api.call"]
    usage = reports[0]["usage"]
    assert usage["simulated"] is True
    assert (usage["llm_calls"], usage["api_calls"]) == (len(llm), len(api))
    assert (usage["tokens_in"], usage["tokens_out"]) == (sum(e.data["tokens_in"] for e in llm), sum(e.data["tokens_out"] for e in llm))
    provisioned = next(e.sim_t for e in api if e.step == "contain.sandbox")
    torn_down = next(e.sim_t for e in api if e.step == "report.teardown")
    assert usage["sandbox_seconds"] == round(torn_down - provisioned, 1) > 0


def test_report_ready_is_raised_in_compile_report_and_agrees_with_the_report(builds, reports):
    for build, assembled in zip(builds, reports, strict=True):
        ready = [e for e in build.log if e.type == "report.ready"]
        assert len(ready) == 1 and ready[0].step == "report.compile" and ready[0].phase == "report"
        assert ready[0].data == report.summary(assembled)
    assert [e.message for e in builds[0].log if e.type == "report.ready"] == ["Report compiled: 14 findings across 3 categories; verdict Completed with findings"]
    assert [e.message for e in builds[1].log if e.type == "report.ready"] == ["Report compiled: 0 findings; verdict Passed"]


def test_no_em_dash_anywhere_in_either_report(reports):
    for assembled in reports:
        text = json.dumps(assembled, ensure_ascii=False)
        assert em_dashes(text) == []


def test_two_runs_of_the_same_build_give_the_same_report(tmp_path, reports):
    async def again():
        manager = StateManager.open(tmp_path)
        manager.apply(demo.load_sample())
        engine = BuildEngine(manager, FakeClock(True))
        engine.set_speed(4)
        engine.start()
        await engine.wait()
        return manager.state.builds[0]

    assert report.assemble(asyncio.run(again())) == reports[0]


# Over HTTP, and across a restart


def test_the_report_endpoint_serves_a_completed_builds_report_and_survives_a_restart(var_dir):
    clock = FakeClock(auto=False)
    with TestClient(create_app(var_dir, clock)) as api:
        assert api.post("/api/demo/sample", json={}).status_code == 201
        assert api.get("/api/builds/b-1/report").json()["detail"]["code"] == "build_not_found"
        assert api.post("/api/builds", json={}).status_code == 201
        running = api.get("/api/builds/b-1/report")
        assert running.status_code == 409 and running.json()["detail"]["code"] == "report_not_ready"
        api.post("/api/demo/skip", json={"to": "build"})
        api.portal.call(clock.advance, 0.05)
        api.portal.call(api.app.state.engine.wait)
        before = api.get("/api/builds/b-1/report")
        assert before.status_code == 200 and before.json()["verdict"]["label"] == "Completed with findings"
    with TestClient(create_app(var_dir)) as api:  # a new process reads the saved state
        after = api.get("/api/builds/b-1/report")
        assert after.status_code == 200 and after.json() == before.json()


# The frontend's fixtures


@pytest.mark.parametrize("name", NAMES)
def test_the_frontend_report_fixtures_are_what_the_backend_assembles(name):
    fixture = FIXTURE_DIR / name
    assert fixture.exists(), f"run: uv run python tests/report_fixtures.py ({name} is missing)"
    assert fixture.read_text(encoding="utf-8") == render(name), f"reports/{name} is stale: run uv run python tests/report_fixtures.py"
