"""M5: the beat engine (build-simulation.md §1 to §4, D-48). The clock is simulated: tests use
FakeClock and never sleep for real. Determinism (NFR-1, AC-8): the same intake and actions
give the same event stream, wall_ts aside, whatever the speed and skips (FR-DC-4)."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any

import pytest

from seedfoundry import demo
from seedfoundry.engine.catalogue import BUDGET_SECONDS, PHASES, TEST_NAMES, TOTAL_WEIGHT
from seedfoundry.engine.clock import FakeClock
from seedfoundry.engine.runner import SLICE, BuildEngine
from seedfoundry.engine.script import GATES, BuildContext, script
from seedfoundry.events import EVENT_TYPES, Event
from seedfoundry.intake import files
from seedfoundry.intake.feedback import FEEDBACK_NAME
from seedfoundry.sample import sample_files
from seedfoundry.state import Category, IntakeFile, StateManager
from test_no_em_dash import em_dashes

ROOT = Path(__file__).resolve().parents[2]
SIMULATION = (ROOT / "docs" / "build-simulation.md").read_text(encoding="utf-8")
FEEDBACK = "The totals do not add up.\n\n- Use bars, not a pie.\n- Label every axis.\n"


def sample() -> list[IntakeFile]:
    return [IntakeFile(id=f"f-{n}", name=name, category=c, content=text) for n, (name, c, text) in enumerate(sample_files(), 1)]


def lab(path: Path, auto: bool = True) -> tuple[StateManager, BuildEngine, FakeClock]:
    manager = StateManager.open(path)
    manager.apply(demo.load_sample())
    clock = FakeClock(auto)
    return manager, BuildEngine(manager, clock), clock


def comparable(events: list[Event]) -> list[dict[str, Any]]:
    return [e.model_dump(mode="json", exclude={"wall_ts"}) for e in events]


def build_events(manager: StateManager, build_id: str = "b-1") -> list[Event]:
    return [e for e in manager.log.after(0) if e.build_id == build_id]


def full_build(path: Path, speed: int = 1) -> tuple[StateManager, FakeClock]:
    async def go():
        manager, engine, clock = lab(path)
        engine.set_speed(speed)
        engine.start()
        await engine.wait()
        return manager, clock

    return asyncio.run(go())


def second_iteration(path: Path, feedback: str | None = FEEDBACK) -> StateManager:
    async def go():
        manager, engine, _ = lab(path)
        engine.start()
        await engine.wait()
        if feedback is not None:
            manager.apply(files.create(FEEDBACK_NAME, Category.MISC_CONTEXT, feedback))
        engine.start(2)
        await engine.wait()
        return manager

    return asyncio.run(go())


@pytest.fixture(scope="module")
def first(tmp_path_factory) -> tuple[StateManager, FakeClock]:
    return full_build(tmp_path_factory.mktemp("first"))


@pytest.fixture(scope="module")
def second(tmp_path_factory) -> StateManager:
    return second_iteration(tmp_path_factory.mktemp("second"))


# The catalogue and the clock (D-7)


def test_weights_sum_to_100_over_a_75_second_budget():
    assert TOTAL_WEIGHT == sum(p.weight for p in PHASES) == 100
    assert BUDGET_SECONDS == 75.0
    assert [p.weight for p in PHASES] == [6, 12, 10, 8, 8, 7, 8, 16, 9, 10, 6]
    assert sum(p.seconds for p in PHASES) == pytest.approx(75.0)


def strike(text: str) -> str:
    return re.sub(r"~~.*?~~", "", text).strip()


def doc_catalogue() -> list[tuple[str, str, int, list[str]]]:
    """(name, code id, weight, test ids) per row of build-simulation.md §2's table."""
    part = SIMULATION.split("## 2. Phase catalogue", 1)[1].split("## 3.", 1)[0]
    rows = []
    for line in part.splitlines():
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) == 6 and cells[0].isdigit():
            rows.append((strike(cells[1]), re.findall(r"`(\w+)`", strike(cells[2]))[0], int(cells[3]), re.findall(r"T-\d\d", cells[5])))
    return rows


def test_the_catalogue_matches_build_simulation_section_2():
    assert doc_catalogue() == [(p.name, p.id, p.weight, [t for t, _ in p.tests]) for p in PHASES]
    part = SIMULATION.split("## 2. Phase catalogue", 1)[1].split("## 3.", 1)[0]
    for phase in PHASES:
        for step in phase.steps:
            assert step.name in part, f"{phase.id}: {step.name}"


def test_a_build_at_1x_takes_75_simulated_seconds(first):
    manager, clock = first
    events = build_events(manager)
    assert events[-1].type == "build.completed"
    assert events[-1].sim_t == BUDGET_SECONDS
    assert 60 <= clock.t <= 90
    assert clock.t == pytest.approx(75.0, abs=0.06)


def test_waits_are_cut_into_slices(first):
    # Speed and skip act within 50 ms because no wait is longer (seed-reuse-notes.md §6.1).
    assert 0 < first[1].longest <= SLICE


@pytest.mark.parametrize("speed", [2, 4])
def test_speed_divides_the_real_time_only(tmp_path, first, speed):
    manager, clock = full_build(tmp_path, speed)
    assert clock.t == pytest.approx(75.0 / speed, abs=0.06)
    assert comparable(build_events(manager)) == comparable(build_events(first[0]))


# Order and shape (build-simulation.md §2, §3)


def check_order(events: list[Event], iteration: int) -> None:
    assert [e.phase for e in events if e.type == "phase.started"] == [p.id for p in PHASES]
    for phase in PHASES:
        steps = [e.step for e in events if e.type == "step.started" and e.phase == phase.id]
        assert steps == [f"{phase.id}.{s.id}" for s in phase.steps_for(iteration)]
    assert [e.code for e in events if e.type == "test.result"] == list(TEST_NAMES)
    # Each step closes before the next opens, each phase likewise.
    open_step = open_phase = None
    for e in events:
        if e.type == "phase.started":
            assert open_phase is None
            open_phase = e.phase
        elif e.type == "phase.completed":
            assert open_phase == e.phase and open_step is None
            open_phase = None
        elif e.type == "step.started":
            assert open_step is None
            open_step = e.step
        elif e.type == "step.completed":
            assert open_step == e.step
            open_step = None
        elif e.type not in ("build.started", "build.completed"):
            assert e.step == open_step and e.phase == open_phase, e.message
    assert events[0].type == "build.started" and events[-1].type == "build.completed"


def test_iteration_1_has_every_phase_step_and_test_in_order(first):
    check_order(build_events(first[0]), 1)


def test_iteration_2_has_every_phase_step_and_test_in_order(second):
    events = build_events(second, "b-2")
    check_order(events, 2)
    assay = [e.step for e in events if e.type == "step.started" and e.phase == "assay"]
    assert assay[:5] == ["assay.feedback-route", "assay.feedback-person", "assay.feedback-instrument", "assay.feedback-environment", "assay.feedback-music"]


def test_seqs_are_contiguous_and_sim_t_never_goes_back(first):
    events = build_events(first[0])
    assert [e.seq for e in events] == list(range(events[0].seq, events[0].seq + len(events)))
    times = [e.sim_t for e in events]
    assert times == sorted(times) and times[0] == 0.0


def test_each_phase_runs_in_its_share_of_the_budget(first):
    events = build_events(first[0])
    start = 0.0
    for phase in PHASES:
        own = [e for e in events if e.phase == phase.id]
        assert own[0].type == "phase.started" and own[0].sim_t == pytest.approx(start)
        start += phase.seconds
        assert own[-1].type == "phase.completed" and own[-1].sim_t == pytest.approx(start)
        assert all(own[0].sim_t <= e.sim_t <= own[-1].sim_t for e in own)


def test_event_types_are_in_the_contract_and_carry_the_build(first):
    for e in build_events(first[0]):
        assert e.type in EVENT_TYPES
        assert e.build_id == "b-1" and e.iteration == 1 and e.sim_t is not None
        assert e.level in ("INFO", "LLM", "API", "TEST", "PASS", "WARN", "FAIL")
        if e.type not in ("build.started", "build.completed"):
            assert e.phase is not None


def strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in strings(v)]
    if isinstance(value, list):
        return [s for v in value for s in strings(v)]
    return []


def test_no_em_dash_in_a_full_builds_log(first, second):
    # NFR-8: every log line, and every string a build event carries, in both iterations.
    for events in (build_events(first[0]), build_events(second, "b-2")):
        for e in events:
            assert em_dashes(e.message) == [], e.message
            assert all(em_dashes(s) == [] for s in strings(e.data)), e.message


def test_simulated_calls_say_so(first):
    calls = [e for e in build_events(first[0]) if e.type in ("llm.call", "api.call")]
    assert len(calls) > 20
    for e in calls:
        assert e.message.endswith("(simulated)") and e.data["simulated"] is True


def test_the_seed_name_is_musics_first_heading(first):
    started = build_events(first[0])[0]
    assert started.message == 'Build started: iteration 1, seed "License Optimization"'
    assert started.data["build"]["seed_name"] == "License Optimization"


# Gates (FR-B-5, D-26, seed-reuse-notes.md §4.2)


def test_three_gates_are_auto_resolved_in_seeding_and_life(first):
    gates = [e for e in build_events(first[0]) if e.type == "gate.auto_resolved"]
    assert [(e.code, e.phase, e.step) for e in gates] == [
        ("servicenow-incident-api", "seeding", "seeding.discovery"),
        ("solution-approval", "seeding", "seeding.assessment"),
        ("close-seeding", "seeding", "seeding.cleanup"),
    ]
    assert [(e.data["basis"]["file"], e.data["basis"]["section"]) for e in gates] == [
        ("environment.md", "Protection Layer"),
        ("music.md", "Decision Logic"),
        ("environment.md", "Protection Layer"),
    ]
    assert [e.data["kind"] for e in gates] == ["credentials", "approval", "confirmation"]
    assert gates[1].message == (
        "Gate solution-approval (approval) auto-resolved: approve License Optimization at potential PARTIAL. Basis: music.md, Decision Logic"
    )
    t11 = next(e for e in build_events(first[0]) if e.code == "T-11")
    assert t11.data["status"] == "pass"


def test_a_gate_without_its_section_resolves_on_default():
    intake = [
        f.model_copy(update={"content": "# Environment\n\n## Styling\n\nPlain.\n"}) if f.category == Category.ENVIRONMENT else f
        for f in sample()
    ]
    beats = script(BuildContext("b-1", 1, intake))
    gates = [e for b in beats for e in b.events if e["type"] == "gate.auto_resolved"]
    assert gates[0]["data"]["basis"] is None
    assert gates[0]["message"].endswith("No matching section in Knowledge, so it resolved on default")
    assert gates[2]["data"]["basis"]["file"] == "music.md"  # close-seeding falls back to Decision Logic


# Stubbed validators (D-51) and boundary advisories (D-12)


def test_stubbed_tests_say_not_run_and_raise_no_finding(first):
    events = build_events(first[0])
    results = {e.code: e.data for e in events if e.type == "test.result"}
    # D-58: T-08 runs from M7, so it left the stubbed list and Germination Trial passes.
    stubbed = [f"T-{n}" for n in range(13, 21)]
    assert sorted(t for t, d in results.items() if d["status"] == "not_run") == stubbed
    for test_id in stubbed:
        assert results[test_id]["arrives_in"] == "M9"
        assert "not run" in results[test_id]["detail"]
    assert all(d["status"] == "pass" for t, d in results.items() if t not in stubbed)
    assert [e for e in events if e.type == "finding.raised"] == []
    phases = {e.phase: e.data["result"] for e in events if e.type == "phase.completed"}
    assert phases["probe"] == phases["harvest"] == "incomplete"
    assert [p for p, r in phases.items() if r != "incomplete"] == ["assay", "distill", "synth", "xexam", "germ", "contain", "plant", "seeding", "report"]
    done = events[-1]
    assert done.data["counts"] == {"pass": 13, "warn": 0, "fail": 0, "not_run": 8}
    assert done.message == "Build completed: 13 tests passed, 8 not run; 0 findings, 0 boundary advisories"


def test_the_data_swap_test_runs_the_same_logic_on_both_estates(first):
    """T-08 (FR-T-2, D-58): real from M7, on the primary and the alternate estate."""
    events = build_events(first[0])
    swap = [e for e in events if e.step == "germ.data-swap" and e.type in ("log", "test.result")]
    assert [e.message for e in swap] == [
        "Primary estate: 13,050 seats, 17 products, 10 vendors; payload for 11 panels, 0 structural problems",
        "Alternate estate: 5,620 seats, 11 products, 8 vendors; payload for 11 panels, 0 structural problems",
        f"Same descriptor ({swap[2].data['descriptor']}) and query engine on 2 estates; payload structure identical",
        "T-08 Data-swap logic unchanged: same descriptor and query engine on both estates, both payloads structurally valid",
    ]
    assert swap[-1].level == "PASS" and swap[-1].data["status"] == "pass" and not swap[-1].data["simulated"]
    assert "arrives_in" not in swap[-1].data
    germ = next(e for e in events if e.type == "phase.completed" and e.phase == "germ")
    assert germ.data["result"] == "passed" and germ.data["tests"] == {"T-07": "pass", "T-08": "pass"}
    collected = next(e for e in events if e.step == "harvest.collect" and e.type == "log")
    assert collected.message == "Collected the License Optimization payload: 11 panels at All products, from 13,050 seat rows in the primary estate"


def test_the_data_swap_test_fails_when_the_logic_gives_another_structure(monkeypatch):
    from seedfoundry import dashboard

    real = dashboard.build

    def drifting(desc, data, *args, **kwargs):
        payload = real(desc, data, *args, **kwargs)
        if data.name == "alternate":
            payload["panels"]["trend"]["series"]["seats_left"] = payload["panels"]["trend"]["series"]["assigned"]
        return payload

    monkeypatch.setattr(dashboard, "build", drifting)
    beats = script(BuildContext("b-1", 1, sample()))
    t08 = next(e for b in beats for e in b.events if e["code"] == "T-08")
    assert t08["data"]["status"] == "fail" and t08["data"]["detail"] == "payload structure differs between the estates"
    germ = next(e for b in beats for e in b.events if e["type"] == "phase.completed" and e["phase"] == "germ")
    assert germ["data"]["result"] == "failed"


def test_boundary_advisories_are_raised_with_file_line_and_home():
    intake = [
        f.model_copy(update={"content": f.content + "\nShow it as a pie chart.\n"}) if f.category == Category.MUSIC else f
        for f in sample()
    ]
    beats = script(BuildContext("b-1", 1, intake))
    events = [e for b in beats for e in b.events]
    raised = [e for e in events if e["type"] == "finding.raised"]
    assert len(raised) == 1
    finding = raised[0]
    assert finding["code"] == "B-UI-1" and finding["level"] == "WARN" and finding["step"] == "assay.boundary"
    line = intake[3].content.split("\n").index("Show it as a pie chart.") + 1
    assert {k: finding["data"][k] for k in ("id", "category", "file", "line", "suggested_home", "severity", "advisory", "phase")} == {
        "id": "B-UI-1",
        "category": "Boundary",
        "file": "music.md",
        "line": line,
        "suggested_home": "environment.md, Styling",
        "severity": "advisory",
        "advisory": True,
        "phase": "assay",
    }
    t03 = next(e for e in events if e["code"] == "T-03")
    assert t03["data"]["status"] == "warn"
    assay = next(e for e in events if e["type"] == "phase.completed" and e["phase"] == "assay")
    assert assay["data"]["result"] == "passed"  # advisories never change the verdict (D-12)
    assert events[-1]["data"]["advisories"] == ["B-UI-1"] and events[-1]["data"]["findings"] == []


# Determinism (NFR-1, AC-8, FR-DC-4)


def test_two_runs_at_different_speeds_and_with_skips_give_the_same_stream(tmp_path, first):
    async def hurried():
        manager, engine, clock = lab(tmp_path, auto=False)
        engine.set_speed(4)
        engine.start()
        await clock.advance(1.5)
        engine.skip("phase")
        await clock.advance(2)
        engine.set_speed(2)
        await clock.advance(4)
        engine.skip("phase")
        engine.skip("phase")
        await clock.advance(3)
        engine.set_speed(1)
        await clock.advance(2.5)
        engine.skip("build")
        await clock.advance(SLICE)
        await engine.wait()
        return manager

    manager = asyncio.run(hurried())
    assert comparable(manager.log.after(0)) == comparable(first[0].log.after(0))
    assert comparable(manager.state.builds[0].log) == comparable(first[0].state.builds[0].log)


def test_the_rng_follows_intake_and_iteration():
    sandbox = lambda beats: next(e["data"]["sandbox_id"] for b in beats for e in b.events if "sandbox_id" in e["data"])  # noqa: E731
    one = script(BuildContext("b-1", 1, sample()))
    assert [(b.sim_t, b.events) for b in one] == [(b.sim_t, b.events) for b in script(BuildContext("b-1", 1, sample()))]
    assert sandbox(one) != sandbox(script(BuildContext("b-1", 2, sample())))
    edited = [f.model_copy(update={"content": f.content + "\nMore.\n"}) if f.category == Category.PERSON else f for f in sample()]
    assert sandbox(one) != sandbox(script(BuildContext("b-1", 1, edited)))


# Pacing: speed, skip and stop (D-48)


def test_skip_phase_plays_the_rest_of_the_phase_at_once_then_paces_again(tmp_path):
    async def go():
        manager, engine, clock = lab(tmp_path, auto=False)
        engine.start()
        await clock.advance(2.0)
        assert build_events(manager)[-1].phase == "assay"
        assert engine.skip("phase") == {"skipping": "phase", "phase": "assay", "name": "Assay"}
        await clock.advance(SLICE)  # within 50 ms
        events = build_events(manager)
        assay_end = PHASES[0].seconds
        assert any(e.type == "phase.completed" and e.phase == "assay" for e in events)
        assert events[-1].sim_t == pytest.approx(assay_end)
        upcoming = engine._beats[engine._next].sim_t
        before = len(events)
        await clock.advance(upcoming - assay_end - 0.01)
        assert len(build_events(manager)) == before  # Distillation is paced again
        await clock.advance(0.02)
        assert len(build_events(manager)) > before
        await engine.stop()

    asyncio.run(go())


def test_a_speed_change_takes_effect_at_once(tmp_path):
    async def go():
        manager, engine, clock = lab(tmp_path, auto=False)
        engine.start()
        await clock.advance(1.0)
        engine.set_speed(4)
        await clock.advance(1.0)  # 1 s at 1x, then 1 s at 4x: 5 simulated seconds
        played = build_events(manager)[-1].sim_t
        assert played <= 5.0 < engine._beats[engine._next].sim_t
        assert played > 4.5
        await engine.stop()

    asyncio.run(go())


def test_skip_to_end_plays_everything_at_once(tmp_path, first):
    async def go():
        manager, engine, clock = lab(tmp_path, auto=False)
        engine.start()
        await clock.advance(3.0)
        assert engine.skip("build") == {"skipping": "build"}
        await clock.advance(SLICE)
        assert manager.state.builds[0].status == "completed"
        await engine.wait()
        return manager

    manager = asyncio.run(go())
    assert comparable(build_events(manager)) == comparable(build_events(first[0]))


def test_stop_cancels_and_nothing_more_is_played(tmp_path):
    async def go():
        manager, engine, clock = lab(tmp_path, auto=False)
        engine.start()
        await clock.advance(5.0)
        count = len(manager.log.after(0))
        await engine.stop()
        await clock.advance(100.0)
        assert len(manager.log.after(0)) == count
        assert not engine.running
        assert manager.state.builds[0].status == "running"  # stop leaves the state to its caller

    asyncio.run(go())


# The finished build's record (D-49)


def test_a_finished_build_keeps_its_own_events(first):
    manager = first[0]
    build = manager.state.builds[0]
    assert build.status == "completed" and build.phase == "report"
    assert build.log == build_events(manager)  # wall_ts included: exactly what was streamed
    assert "log" not in manager.snapshot()["builds"][0]
    assert manager.store.load()["builds"][0]["log"][0]["type"] == "build.started"
    assert not manager.state.build_running


# Iteration 2 before M10 routing (D-52)


def test_iteration_2_reads_the_feedback_and_claims_no_edit(second):
    events = build_events(second, "b-2")
    lines = [e.message for e in events if e.type == "log" and e.step and e.step.startswith("assay.feedback")]
    assert lines[:2] == [
        f"Read {FEEDBACK_NAME}: 3 segments, {len(FEEDBACK)} bytes",
        "Routing feedback to the Ensemble files arrives in M10, so no segment was routed",
    ]
    for name in ("person.md", "instrument-awareness.md", "environment.md", "music.md"):
        assert f"{name}: no change, no feedback was routed to it" in lines
    completed = [e.message for e in events if e.type == "step.completed" and e.step.startswith("assay.feedback-") and e.step != "assay.feedback-route"]
    assert all(m.endswith(": no change") for m in completed) and len(completed) == 4
    assert not [e for e in events if e.type == "llm.call" and e.phase == "assay"]  # no routing decision was made
    # The four core files are exactly the sample's.
    core = {f.name: f.content for f in second.state.intake.files if f.category != Category.MISC_CONTEXT}
    assert core == {name: text for name, c, text in sample_files() if c != Category.MISC_CONTEXT}
    prior = [e.message for e in events if e.step == "distill.feedback" and e.type == "log"]
    assert prior == [
        f"Observer feedback: {len(FEEDBACK)} characters, 3 segments",
        "Prior findings from iteration 1: 0",
        "No prior findings, so there are no corrections to plan",
    ]


def test_iteration_2_without_a_feedback_file_says_so(tmp_path):
    manager = second_iteration(tmp_path, feedback=None)
    events = build_events(manager, "b-2")
    route = [e.message for e in events if e.step == "assay.feedback-route" and e.type == "log"]
    assert route == [f"No {FEEDBACK_NAME} in Knowledge, so there is no observer feedback to route"]
