"""M10: the rebuild over HTTP (FR-RB-3 to FR-RB-8, FR-R-3, AC-3, D-67 to D-69). Iteration 1, then
the rebuild with the demo's feedback in one request, then iteration 2 with zero findings, its
report listing all 14 iteration 1 findings as resolved and quoting the feedback; the feedback file
in Knowledge; the four core files changed exactly as iteration 2's lines say; iteration 1's file
versions kept with build 1; a refused or failed rebuild leaves nothing half done; the same flow
twice gives the same events, edits and report; a restart keeps them."""

from __future__ import annotations

import difflib
import re

import pytest
from fastapi.testclient import TestClient

from seedfoundry.engine.clock import FakeClock
from seedfoundry.engine.runner import SLICE
from seedfoundry.intake.feedback import FEEDBACK_NAME
from seedfoundry.main import create_app
from seedfoundry.sample import demo_feedback, sample_files
from test_no_em_dash import em_dashes

CATALOGUE = ["N-1", "N-2", "N-3", "N-4", "N-5", "V-1", "V-2", "V-3", "V-4", "V-5", "V-6", "V-7", "V-8", "L-1"]
CORE = ("person.md", "instrument-awareness.md", "environment.md", "music.md")


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(auto=False)


@pytest.fixture
def api(var_dir, clock):
    with TestClient(create_app(var_dir, clock)) as client:
        yield client


def finish(client: TestClient, clock: FakeClock) -> None:
    assert client.post("/api/demo/skip", json={"to": "build"}).status_code == 200
    client.portal.call(clock.advance, SLICE)
    client.portal.call(client.app.state.engine.wait)


def first_iteration(client: TestClient, clock: FakeClock) -> None:
    assert client.post("/api/demo/sample", json={}).status_code == 201
    assert client.post("/api/builds", json={}).status_code == 201
    finish(client, clock)


def rebuild(client: TestClient, feedback: str):
    return client.post("/api/builds", json={"iteration": 2, "feedback": feedback})


def files_by_name(client: TestClient) -> dict[str, dict]:
    return {f["name"]: f for f in client.get("/api/intake/files").json()}


def two_iterations(client: TestClient, clock: FakeClock) -> None:
    first_iteration(client, clock)
    started = rebuild(client, demo_feedback())
    assert started.status_code == 201 and started.json()["iteration"] == 2
    finish(client, clock)


def test_the_full_two_iteration_flow(api, clock):
    two_iterations(api, clock)
    state = api.get("/api/state").json()
    assert state["iteration"] == 2
    assert [(b["id"], b["iteration"], b["status"]) for b in state["builds"]] == [("b-1", 1, "completed"), ("b-2", 2, "completed")]
    # The feedback is a Misc Context file in the Knowledge list (FR-RB-4).
    feedback = files_by_name(api)[FEEDBACK_NAME]
    assert feedback["category"] == "misc_context" and feedback["content"] == demo_feedback()
    # Iteration 2 completes with zero findings (AC-3).
    second = api.get("/api/builds/b-2/report").json()
    assert second["verdict"]["label"] == "Passed" and second["counts"]["findings"] == 0
    assert second["counts"]["advisories"] == 0  # the demo's feedback raises no boundary advisory
    # Changes since iteration 1 (FR-R-3): all 14 resolved, the feedback quoted.
    changes = second["changes"]
    assert [f["id"] for f in changes["findings"]] == CATALOGUE
    assert all(f["status"] == "resolved" for f in changes["findings"]) and (changes["resolved"], changes["open"]) == (14, 0)
    assert changes["prior_build_id"] == "b-1"
    assert changes["feedback"] == {"name": FEEDBACK_NAME, "content": demo_feedback(), "segments": 10}
    assert {u["file"] for u in changes["updates"]} == set(CORE) and changes["kept"] == [10]
    assert api.get("/api/builds/b-1/report").json()["changes"] is None
    assert em_dashes(str(second)) == []


def test_the_log_lines_match_the_edits_actually_made(api, clock):
    two_iterations(api, clock)
    kept = {f["name"]: f["content"] for f in api.get("/api/builds/b-1/files").json()["files"]}
    now = files_by_name(api)
    events = api.get("/api/builds/b-2/events").json()["events"]
    lines = [e for e in events if e["type"] == "log" and (e["step"] or "").startswith("assay.feedback-") and e["data"].get("lines_added")]
    claimed: dict[str, int] = {}
    for line in lines:
        name, section, added, numbers = (line["data"][k] for k in ("file", "section", "lines_added", "segments"))
        assert re.fullmatch(rf"{re.escape(name)}: \+{added} lines? in {re.escape(section)} \(segments? [\d, ]+\)", line["message"])
        claimed[name] = claimed.get(name, 0) + added
        # Each segment the line names is in that section of the file now, verbatim.
        section_text = now[name]["content"].split(f"\n## {section}\n", 1)[1].split("\n## ", 1)[0]
        route = {e["data"]["segment"]: e for e in events if e["step"] == "assay.feedback-route" and "segment" in e["data"]}
        for number in numbers:
            assert route[number]["data"]["section"] == section and route[number]["data"]["file"] == name
            assert f"### Observer feedback (iteration 1)" in section_text
    for name in CORE:
        before, after = kept[name].split("\n"), now[name]["content"].split("\n")
        ops = difflib.SequenceMatcher(a=before, b=after, autojunk=False).get_opcodes()
        assert {op for op, *_ in ops} == {"equal", "insert"}
        assert sum(j2 - j1 for op, _, _, j1, j2 in ops if op == "insert") == claimed[name]
    assert claimed == {"person.md": 4, "instrument-awareness.md": 4, "environment.md": 18, "music.md": 4}


def test_iteration_1s_file_versions_are_kept_with_build_1(api, clock):
    two_iterations(api, clock)
    kept = api.get("/api/builds/b-1/files").json()
    assert kept["iteration"] == 1
    assert [(f["name"], f["content"]) for f in kept["files"]] == [(name, text) for name, _, text in sample_files()]
    second = {f["name"]: f["content"] for f in api.get("/api/builds/b-2/files").json()["files"]}
    assert second == {name: f["content"] for name, f in files_by_name(api).items()}  # what iteration 2 built from
    assert "files" not in api.get("/api/state").json()["builds"][0]  # the snapshot leaves them out
    assert api.get("/api/builds/b-9/files").json()["detail"]["code"] == "build_not_found"


def test_the_files_change_as_their_update_sub_steps_play(api, clock):
    first_iteration(api, clock)
    since = api.get("/api/state").json()["seq"]
    rebuild(api, demo_feedback())
    log = api.app.state.lab.log
    # Before the Update sub-steps play, Knowledge holds the sample's core files and the new feedback file.
    assert {n: files_by_name(api)[n]["content"] for n in CORE} == {n: t for n, _, t in sample_files() if n in CORE}
    assert [e.type for e in log.after(since)][:2] == ["intake.file_created", "build.started"]
    finish(api, clock)
    intake = [e for e in log.after(since) if e.type.startswith("intake.")]
    assert [(e.type, e.data["file"]["name"], e.data["source"]) for e in intake] == [
        ("intake.file_created", FEEDBACK_NAME, "rebuild"),
        *[("intake.file_updated", name, "feedback") for name in CORE],
    ]
    assert all(e.build_id is None and e.sim_t is None for e in intake)  # the intake shape (D-32)
    assert not [e for e in api.get("/api/builds/b-2/events").json()["events"] if e["type"].startswith("intake.")]
    # Each file changes right after the Update line that names it.
    stream = list(log.after(since))
    for event in intake[1:]:
        before = stream[stream.index(event) - 1]
        assert before.step.startswith("assay.feedback-") and before.data["file"] == event.data["file"]["name"]


def test_start_rebuild_needs_feedback_and_a_refusal_leaves_nothing(api, clock):
    first_iteration(api, clock)
    seq = api.get("/api/state").json()["seq"]
    for feedback in ("", "  \n\t "):
        refused = rebuild(api, feedback)
        assert refused.status_code == 422 and refused.json()["detail"]["code"] == "feedback_empty"
    assert rebuild(api, "x\x00").json()["detail"]["code"] == "not_utf8_text"
    assert api.get("/api/state").json()["seq"] == seq
    assert FEEDBACK_NAME not in files_by_name(api) and len(api.get("/api/state").json()["builds"]) == 1


def test_a_failed_save_leaves_neither_the_file_nor_the_build(api, clock, monkeypatch):
    first_iteration(api, clock)
    before = api.get("/api/state").json()

    real = api.app.state.lab.store.save

    def broken(document):
        # Only the save that would hold iteration 2 fails: a rebuild that saved the file first, in a
        # change of its own, would leave the file behind.
        if any(b["iteration"] == 2 for b in document["builds"]):
            raise OSError("disk full")
        real(document)

    monkeypatch.setattr(api.app.state.lab.store, "save", broken)
    with pytest.raises(OSError):
        rebuild(api, demo_feedback())
    monkeypatch.undo()
    assert api.get("/api/state").json() == before
    assert not api.app.state.engine.running


def test_an_existing_feedback_file_is_rewritten_in_place(api, clock):
    first_iteration(api, clock)
    made = api.post("/api/intake/files", json={"name": FEEDBACK_NAME, "category": "misc_context", "content": "Draft."}).json()
    assert rebuild(api, "The totals do not add up.").status_code == 201
    finish(api, clock)
    named = [f for f in api.get("/api/intake/files").json() if f["name"] == FEEDBACK_NAME]
    assert [(f["id"], f["content"]) for f in named] == [(made["id"], "The totals do not add up.")]


def test_rebuild_is_offered_once(api, clock):
    two_iterations(api, clock)
    again = rebuild(api, "More feedback.")
    assert again.status_code == 409 and again.json()["detail"]["code"] == "wrong_iteration"
    # A later start of iteration 2 (OQ-19) builds from the feedback already in Knowledge, adding nothing twice.
    before = {n: f["content"] for n, f in files_by_name(api).items()}
    assert api.post("/api/builds", json={}).status_code == 201
    finish(api, clock)
    assert {n: f["content"] for n, f in files_by_name(api).items()} == before
    events = api.get("/api/builds/b-3/events").json()["events"]
    assert "Intake unchanged: 0 files changed" in " ".join(e["message"] for e in events)
    assert api.get("/api/builds/b-3/report").json()["verdict"]["label"] == "Passed"


def test_the_demo_feedback_is_served_for_prefill(api):
    assert api.get("/api/demo/feedback").json() == {"name": FEEDBACK_NAME, "content": demo_feedback()}


# Determinism (NFR-1) and a restart


def comparable(events: list[dict]) -> list[dict]:
    return [{k: v for k, v in e.items() if k != "wall_ts"} for e in events]


def test_the_same_flow_twice_gives_the_same_events_edits_and_report(tmp_path):
    runs = []
    for name in ("one", "two"):
        clock = FakeClock(auto=False)
        with TestClient(create_app(tmp_path / name, clock)) as client:
            two_iterations(client, clock)
            runs.append(
                (
                    comparable([e.model_dump(mode="json") for e in client.app.state.lab.log.after(0)]),
                    {n: f["content"] for n, f in files_by_name(client).items()},
                    client.get("/api/builds/b-2/report").json(),
                )
            )
    assert runs[0] == runs[1]


def test_reports_and_files_survive_a_restart(var_dir):
    clock = FakeClock(auto=False)
    with TestClient(create_app(var_dir, clock)) as client:
        two_iterations(client, clock)
        before = [client.get(path).json() for path in ("/api/builds/b-1/report", "/api/builds/b-2/report", "/api/builds/b-1/files", "/api/intake/files")]
    with TestClient(create_app(var_dir)) as client:
        assert [client.get(path).json() for path in ("/api/builds/b-1/report", "/api/builds/b-2/report", "/api/builds/b-1/files", "/api/intake/files")] == before


def test_a_finding_iteration_2_still_raises_reads_open(api, clock):
    from seedfoundry import report

    two_iterations(api, clock)
    first, second = (b.model_copy(deep=True) for b in api.app.state.lab.state.builds)
    kept = next(e for e in first.log if e.type == "finding.raised" and e.code == "V-3")
    second.log.insert(len(second.log) - 1, kept.model_copy(update={"build_id": second.id}))
    changes = report.assemble(second, first)["changes"]
    assert (changes["resolved"], changes["open"]) == (13, 1)
    assert [f["id"] for f in changes["findings"] if f["status"] == "open"] == ["V-3"]
