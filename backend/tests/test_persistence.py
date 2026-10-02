"""M1: state survives a server restart (FR-IN-10, D-3), writes are atomic,
and a failed save changes nothing."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from seedfoundry.main import create_app
from seedfoundry.state import Build, State, StateManager
from seedfoundry.store import JsonStore, StoreError


def test_store_round_trip(tmp_path):
    store = JsonStore(tmp_path / "var" / "doc.json")
    assert store.load() is None
    store.save({"a": [1, 2], "text": "Café"})
    assert store.load() == {"a": [1, 2], "text": "Café"}
    assert [p.name for p in (tmp_path / "var").iterdir()] == ["doc.json"]


def test_failed_rename_keeps_the_old_document(tmp_path, monkeypatch):
    store = JsonStore(tmp_path / "doc.json")
    store.save({"version": 1})

    def broken_replace(source, target):
        raise OSError("disk full")

    monkeypatch.setattr("seedfoundry.store.os.replace", broken_replace)
    with pytest.raises(OSError):
        store.save({"version": 2})
    assert store.load() == {"version": 1}
    assert [p.name for p in tmp_path.iterdir()] == ["doc.json"]


def test_corrupt_document_fails_loudly(tmp_path):
    (tmp_path / "doc.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(StoreError, match="doc.json is not valid JSON"):
        JsonStore(tmp_path / "doc.json").load()


def test_nothing_is_written_until_something_changes(var_dir):
    with TestClient(create_app(var_dir)) as client:
        client.get("/api/state")
    assert not (var_dir / "state.json").exists()


def test_intake_survives_an_app_restart(var_dir):
    with TestClient(create_app(var_dir)) as client:
        client.post("/api/intake/files", json={"name": "person.md", "category": "person", "content": "# Person"})
        client.post("/api/intake/import", params={"filename": "music.md"}, content=b"# License Optimization")
        client.patch("/api/intake/files/f-1", json={"name": "player.md"})
        before = client.get("/api/state").json()
    with TestClient(create_app(var_dir)) as client:
        after = client.get("/api/state").json()
        assert after == before
        assert [f["name"] for f in after["intake"]["files"]] == ["player.md", "music.md"]
        # Seq and file ids carry on, they do not restart at 1.
        created = client.post("/api/intake/files", json={"name": "n.md", "category": "misc_context"}).json()
        assert created["id"] == "f-3"
        assert client.get("/api/state").json()["seq"] == before["seq"] + 1


def test_saved_document_is_the_snapshot(var_dir):
    with TestClient(create_app(var_dir)) as client:
        client.post("/api/intake/files", json={"name": "a.md", "category": "misc_context"})
        snapshot = client.get("/api/state").json()
    assert json.loads((var_dir / "state.json").read_text(encoding="utf-8")) == snapshot


def test_failed_save_changes_nothing(var_dir, monkeypatch):
    with TestClient(create_app(var_dir)) as client:
        client.post("/api/intake/files", json={"name": "a.md", "category": "misc_context"})
        lab = client.app.state.lab
        before = client.get("/api/state").json()

        def broken_save(document):
            raise OSError("disk full")

        monkeypatch.setattr(lab.store, "save", broken_save)
        with pytest.raises(OSError):
            client.post("/api/intake/files", json={"name": "b.md", "category": "misc_context"})
        monkeypatch.undo()
        assert client.get("/api/state").json() == before
        assert lab.log.last_seq == before["seq"]


def test_running_build_is_interrupted_on_restart(var_dir):
    store = JsonStore(var_dir / "state.json")
    store.save(State(seq=7, builds=[Build(id="b-1", iteration=1)]).model_dump(mode="json"))
    manager = StateManager.open(var_dir)
    assert manager.state.builds[0].status == "interrupted"
    assert manager.state.seq == 8
    [event] = manager.log.after(7)
    assert (event.seq, event.type, event.build_id, event.level) == (8, "build.interrupted", "b-1", "WARN")
    assert store.load()["builds"][0]["status"] == "interrupted"


def test_intake_is_editable_after_an_interrupted_build(var_dir):
    JsonStore(var_dir / "state.json").save(State(builds=[Build(id="b-1", iteration=1)]).model_dump(mode="json"))
    with TestClient(create_app(var_dir)) as client:
        response = client.post("/api/intake/files", json={"name": "a.md", "category": "misc_context"})
        assert response.status_code == 201


def test_file_survives_a_real_server_restart(server):
    """The M1 hand check, automated: create a file through the API, kill the
    server process, start it again, and the file is still there."""
    server.start()
    status, created = server.request(
        "POST", "/api/intake/files", {"name": "person.md", "category": "person", "content": "# Person\n"}
    )
    assert status == 201
    server.kill()
    server.start()
    status, found = server.request("GET", f"/api/intake/files/{created['id']}")
    assert status == 200
    assert found == created
