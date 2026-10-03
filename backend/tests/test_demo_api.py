"""M4: the demo controller's server actions (D-46). Load sample Seed fills intake
with the sample (FR-DC-2, FR-DC-3) and replaces existing files only when asked
(OQ-17); Load sample and Clear intake keep the intake rules (FR-B-8); Reset to
start returns to a fresh start. All of them emit the normal events."""

from __future__ import annotations

from seedfoundry.sample import SAMPLE_FILES, sample_files
from seedfoundry.state import Approval, Build

SAMPLE_NAMES = [name for name, _ in SAMPLE_FILES]
CORE = ["person", "instrument_awareness", "environment", "music"]


def load(client, replace=False):
    return client.post("/api/demo/sample", json={"replace": replace})


def create(client, name="notes.md", category="misc_context", content="text"):
    return client.post("/api/intake/files", json={"name": name, "category": category, "content": content})


def events(client, after=0):
    return list(client.app.state.lab.log.after(after))


def seq(client):
    return client.get("/api/state").json()["seq"]


def start_fake_build(client):
    client.app.state.lab.state.builds.append(Build(id="b-1", iteration=1))


# Load sample Seed


def test_load_sample_fills_the_four_core_slots(client):
    response = load(client)
    assert response.status_code == 201
    files = client.get("/api/intake/files").json()
    assert [(f["name"], f["category"]) for f in files] == [
        ("person.md", "person"),
        ("instrument-awareness.md", "instrument_awareness"),
        ("environment.md", "environment"),
        ("music.md", "music"),
        ("vendor-notes.md", "misc_context"),
    ]
    # A slot is complete when its file holds something other than whitespace (D-42 (a)).
    for category in CORE:
        holders = [f for f in files if f["category"] == category]
        assert len(holders) == 1 and holders[0]["content"].strip()


def test_load_sample_returns_the_files_with_content(client):
    body = load(client).json()
    assert [f["id"] for f in body] == ["f-1", "f-2", "f-3", "f-4", "f-5"]
    assert body == client.get("/api/intake/files").json()


def test_load_sample_emits_one_create_per_file(client):
    load(client)
    seen = [(e.type, e.data["file"]["name"], e.data["source"]) for e in events(client)]
    assert seen == [("intake.file_created", name, "sample") for name in SAMPLE_NAMES]
    assert events(client)[0].message == "Loaded person.md (Person)"


def test_the_seed_name_is_music_md_first_heading(client):
    # OQ-7: the Seed name is the first heading of music.md.
    load(client)
    music = next(f for f in client.get("/api/intake/files").json() if f["category"] == "music")
    assert music["content"].splitlines()[0] == "# License Optimization"


def test_load_sample_refuses_a_filled_intake_unless_replace(client):
    create(client, "my-notes.md")
    before = seq(client)
    refused = load(client)
    assert refused.status_code == 409
    detail = refused.json()["detail"]
    assert detail["code"] == "intake_not_empty"
    assert detail["files"] == 1
    assert detail["message"] == "Knowledge has 1 file. Loading the sample Seed replaces them all."
    assert [f["name"] for f in client.get("/api/intake/files").json()] == ["my-notes.md"]
    assert seq(client) == before


def test_load_sample_with_replace_deletes_every_file_first(client):
    # OQ-17: replace all, Misc Context included.
    create(client, "person.md", "person", "mine")
    create(client, "my-notes.md")
    after = seq(client)
    assert load(client, replace=True).status_code == 201
    assert [f["name"] for f in client.get("/api/intake/files").json()] == SAMPLE_NAMES
    seen = [(e.type, e.data["file"]["name"]) for e in events(client, after)]
    assert seen == [
        ("intake.file_deleted", "person.md"),
        ("intake.file_deleted", "my-notes.md"),
        *[("intake.file_created", name) for name in SAMPLE_NAMES],
    ]


def test_load_sample_on_an_empty_intake_with_replace_just_loads(client):
    assert load(client, replace=True).status_code == 201
    assert [e.type for e in events(client)] == ["intake.file_created"] * len(SAMPLE_NAMES)


def test_load_sample_is_refused_while_a_build_runs(client):
    start_fake_build(client)
    for replace in (False, True):
        response = load(client, replace)
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "intake_locked"
    assert client.get("/api/intake/files").json() == []


# Clear intake


def test_clear_deletes_every_file(client):
    load(client)
    after = seq(client)
    response = client.post("/api/demo/clear")
    assert response.status_code == 200
    assert response.json() == {"deleted": 5}
    assert client.get("/api/intake/files").json() == []
    assert [(e.type, e.data["file"]["name"]) for e in events(client, after)] == [
        ("intake.file_deleted", name) for name in SAMPLE_NAMES
    ]


def test_clear_on_an_empty_intake_changes_nothing(client):
    assert client.post("/api/demo/clear").json() == {"deleted": 0}
    assert seq(client) == 0


def test_clear_is_refused_while_a_build_runs(client):
    create(client)
    start_fake_build(client)
    response = client.post("/api/demo/clear")
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "intake_locked"
    assert len(client.get("/api/intake/files").json()) == 1


# Reset to start


def test_reset_returns_to_a_fresh_start(client):
    load(client)
    lab = client.app.state.lab
    lab.state.builds.append(Build(id="b-1", iteration=1, status="completed"))
    lab.state.builds.append(Build(id="b-2", iteration=2, status="running"))
    lab.state.iteration = 2
    lab.state.approval = Approval(iteration=2)
    after = seq(client)
    response = client.post("/api/demo/reset")
    assert response.status_code == 200
    assert response.json() == {"files_removed": 5, "builds_removed": 2}
    state = client.get("/api/state").json()
    assert (state["intake"]["files"], state["builds"], state["approval"], state["iteration"]) == ([], [], None, 1)
    seen = [e.type for e in events(client, after)]
    assert seen == ["intake.file_deleted"] * 5 + ["demo.reset"]
    last = events(client, after)[-1]
    assert last.message == "Reset to start: 5 files and 2 builds removed"
    assert last.data == {"files_removed": 5, "builds_removed": 2}


def test_reset_works_while_a_build_runs(client):
    create(client)
    start_fake_build(client)
    assert client.post("/api/demo/reset").status_code == 200
    assert client.get("/api/state").json()["builds"] == []
    # Intake is editable again.
    assert create(client).status_code == 201


def test_reset_keeps_the_seq_and_the_file_id_counter(client):
    load(client)
    client.post("/api/demo/reset")
    before = seq(client)
    assert before > 0
    assert create(client).json()["id"] == "f-6"
    assert seq(client) == before + 1


def test_reset_with_nothing_to_reset_emits_nothing(client):
    assert client.post("/api/demo/reset").json() == {"files_removed": 0, "builds_removed": 0}
    assert seq(client) == 0


def test_demo_changes_survive_a_restart(var_dir):
    from fastapi.testclient import TestClient

    from seedfoundry.main import create_app

    with TestClient(create_app(var_dir)) as first:
        load(first)
    with TestClient(create_app(var_dir)) as second:
        files = second.get("/api/intake/files").json()
        assert [(f["name"], f["content"]) for f in files] == [(name, content) for name, _, content in sample_files()]
