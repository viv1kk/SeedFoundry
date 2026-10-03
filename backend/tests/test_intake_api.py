"""M1: intake CRUD, import, the one-per-core replace rule (FR-IN-3), the
size and encoding limits (FR-IN-11), filename hints (FR-IN-7) and the
read-only lock while a build runs (FR-B-8)."""

from __future__ import annotations

import pytest

from seedfoundry.intake.files import MAX_FILE_BYTES
from seedfoundry.state import Build


def create(client, name="notes.md", category="misc_context", content="text", **extra):
    return client.post("/api/intake/files", json={"name": name, "category": category, "content": content, **extra})


def imported(client, filename, raw, **params):
    return client.post("/api/intake/import", params={"filename": filename, **params}, content=raw)


def names(client):
    return sorted(f["name"] for f in client.get("/api/intake/files").json())


# CRUD


def test_create_then_read(client):
    response = create(client, "person.md", "person", "# Person\n")
    assert response.status_code == 201
    created = response.json()
    assert created == {"id": "f-1", "name": "person.md", "category": "person", "content": "# Person\n", "size": 9}
    assert client.get("/api/intake/files/f-1").json() == created
    assert client.get("/api/intake/files").json() == [created]


def test_file_ids_follow_creation_order(client):
    ids = [create(client, f"n{i}.md").json()["id"] for i in range(3)]
    assert ids == ["f-1", "f-2", "f-3"]


def test_rename(client):
    create(client, "draft.md")
    response = client.patch("/api/intake/files/f-1", json={"name": "vendor-notes.md"})
    assert response.status_code == 200
    assert response.json()["name"] == "vendor-notes.md"
    assert names(client) == ["vendor-notes.md"]


def test_change_category(client):
    create(client, "music.md", "misc_context")
    response = client.patch("/api/intake/files/f-1", json={"category": "music"})
    assert response.status_code == 200
    assert response.json()["category"] == "music"


def test_update_content(client):
    create(client, "notes.md", content="old")
    response = client.patch("/api/intake/files/f-1", json={"content": "new text"})
    assert response.json()["content"] == "new text"
    assert response.json()["size"] == 8
    assert client.get("/api/intake/files/f-1").json()["content"] == "new text"


def test_delete(client):
    create(client, "a.md")
    create(client, "b.md")
    assert client.delete("/api/intake/files/f-1").status_code == 204
    assert names(client) == ["b.md"]
    assert client.get("/api/intake/files/f-1").status_code == 404


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_unknown_file_is_404(client, method):
    kwargs = {"json": {"name": "x.md"}} if method == "patch" else {}
    response = getattr(client, method)("/api/intake/files/f-99", **kwargs)
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "file_not_found"


@pytest.mark.parametrize("bad", ["", "   ", "a/b.md", "a\\b.md", "x" * 121])
def test_bad_names_are_refused(client, bad):
    response = create(client, bad)
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_name"


def test_unknown_category_is_refused(client):
    assert create(client, "x.md", "vibes").status_code == 422


def test_names_are_trimmed(client):
    assert create(client, "  notes.md  ").json()["name"] == "notes.md"


def test_line_ends_are_normalised(client):
    assert create(client, content="a\r\nb\rc\n").json()["content"] == "a\nb\nc\n"


def test_patch_that_changes_nothing_emits_no_event(client):
    create(client, "notes.md", content="same")
    seq = client.get("/api/state").json()["seq"]
    client.patch("/api/intake/files/f-1", json={"name": "notes.md", "content": "same"})
    assert client.get("/api/state").json()["seq"] == seq


# One per core category (FR-IN-3)


CORE = ["person", "instrument_awareness", "environment", "music"]


@pytest.mark.parametrize("category", CORE)
def test_second_core_file_is_refused_without_replace(client, category):
    create(client, "first.md", category)
    response = create(client, "second.md", category)
    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "core_slot_taken"
    assert detail["existing"]["name"] == "first.md"
    assert "Replace" in detail["message"]
    assert names(client) == ["first.md"]


@pytest.mark.parametrize("category", CORE)
def test_replace_swaps_the_core_file(client, category):
    create(client, "first.md", category)
    response = create(client, "second.md", category, replace=True)
    assert response.status_code == 201
    files = client.get("/api/intake/files").json()
    assert [(f["name"], f["category"]) for f in files] == [("second.md", category)]


def test_replace_on_a_free_slot_just_creates(client):
    assert create(client, "person.md", "person", replace=True).status_code == 201


def test_misc_context_is_unlimited(client):
    for i in range(5):
        assert create(client, f"note-{i}.md", "misc_context").status_code == 201
    assert len(names(client)) == 5


def test_category_change_into_a_taken_slot_needs_replace(client):
    create(client, "person.md", "person")
    create(client, "player.md", "misc_context")
    refused = client.patch("/api/intake/files/f-2", json={"category": "person"})
    assert refused.status_code == 409
    assert refused.json()["detail"]["existing"]["id"] == "f-1"
    allowed = client.patch("/api/intake/files/f-2", json={"category": "person", "replace": True})
    assert allowed.status_code == 200
    assert [f["id"] for f in client.get("/api/intake/files").json()] == ["f-2"]


def test_core_file_can_be_saved_in_its_own_slot(client):
    create(client, "person.md", "person")
    response = client.patch("/api/intake/files/f-1", json={"category": "person", "content": "edited"})
    assert response.status_code == 200


def test_import_into_a_taken_slot_needs_replace(client):
    imported(client, "person.md", b"# One")
    refused = imported(client, "player.md", b"# Two")
    assert refused.status_code == 409
    assert refused.json()["detail"]["code"] == "core_slot_taken"
    allowed = imported(client, "player.md", b"# Two", replace="true")
    assert allowed.status_code == 201
    assert names(client) == ["player.md"]


def test_replace_emits_delete_then_create(client):
    create(client, "first.md", "music")
    create(client, "second.md", "music", replace=True)
    lab = client.app.state.lab
    types = [(e.type, e.data["file"]["name"]) for e in lab.log.after(0)]
    assert types == [
        ("intake.file_created", "first.md"),
        ("intake.file_deleted", "first.md"),
        ("intake.file_created", "second.md"),
    ]


# Import and filename hints (FR-IN-7)


@pytest.mark.parametrize(
    ("filename", "category"),
    [
        ("person.md", "person"),
        ("player.md", "person"),
        ("instrument-awareness.md", "instrument_awareness"),
        ("instrument_awareness.md", "instrument_awareness"),
        ("environment.md", "environment"),
        ("music.md", "music"),
        ("Music.MD", "music"),
        ("vendor-notes.md", "misc_context"),
    ],
)
def test_import_preselects_category_from_filename(client, filename, category):
    response = imported(client, filename, b"# Heading\n")
    assert response.status_code == 201
    assert response.json()["category"] == category
    assert response.json()["name"] == filename


def test_import_category_overrides_the_hint(client):
    assert imported(client, "person.md", b"x", category="misc_context").json()["category"] == "misc_context"


def test_import_keeps_only_the_base_name(client):
    assert imported(client, "C:\\Users\\me\\music.md", b"x").json()["name"] == "music.md"


def test_import_strips_a_utf8_bom(client):
    assert imported(client, "notes.md", "\ufeff# Notes".encode()).json()["content"] == "# Notes"


def test_import_keeps_utf8_text(client):
    text = "Café, naïve, 東京, emoji 🌱\n"
    assert imported(client, "notes.md", text.encode()).json()["content"] == text


def test_import_accepts_md_only(client):
    response = imported(client, "notes.txt", b"text")
    assert response.status_code == 415
    assert response.json()["detail"]["code"] == "not_markdown"


def test_categories_endpoint_serves_labels_and_hints(client):
    body = client.get("/api/intake/categories").json()
    assert [c["label"] for c in body["categories"]] == [
        "Person",
        "Instrument Awareness",
        "Environment",
        "Music",
        "Misc Context",
    ]
    assert [c["core"] for c in body["categories"]] == [True, True, True, True, False]
    assert body["filename_hints"]["player.md"] == "person"
    assert body["max_file_bytes"] == 1024 * 1024


def test_categories_endpoint_serves_one_line_descriptions(client):
    # The Knowledge page's empty state explains each category from here (ui-spec.md §2), so
    # the frontend keeps no copy of the category list.
    body = client.get("/api/intake/categories").json()
    descriptions = [c["description"] for c in body["categories"]]
    assert all(d.strip() and "\n" not in d for d in descriptions)
    assert len(set(descriptions)) == len(descriptions)


# Size and encoding (FR-IN-11)


def test_exactly_one_megabyte_is_accepted(client):
    assert MAX_FILE_BYTES == 1_048_576
    assert imported(client, "big.md", b"a" * MAX_FILE_BYTES).status_code == 201
    assert create(client, "big2.md", content="a" * MAX_FILE_BYTES).status_code == 201


def test_one_byte_over_is_refused_on_import(client):
    response = imported(client, "big.md", b"a" * (MAX_FILE_BYTES + 1))
    assert response.status_code == 413
    detail = response.json()["detail"]
    assert detail["code"] == "file_too_large"
    assert detail["message"] == "big.md is 1,048,577 bytes. Files are limited to 1 MB (1,048,576 bytes)."
    assert names(client) == []


def test_size_counts_utf8_bytes_not_characters(client):
    # 'é' is two bytes in UTF-8.
    response = create(client, content="é" * (MAX_FILE_BYTES // 2 + 1))
    assert response.status_code == 413


def test_oversized_content_update_is_refused(client):
    create(client, "notes.md", content="small")
    response = client.patch("/api/intake/files/f-1", json={"content": "a" * (MAX_FILE_BYTES + 1)})
    assert response.status_code == 413
    assert client.get("/api/intake/files/f-1").json()["content"] == "small"


@pytest.mark.parametrize(
    "raw",
    [
        b"\x89PNG\r\n\x1a\n\x00\x00",  # binary
        "caf\u00e9".encode("latin-1"),  # not UTF-8
        "# Notes".encode("utf-16"),  # UTF-16 with BOM
        b"text with a \x00 byte",  # valid UTF-8 but not text
    ],
)
def test_non_utf8_text_is_refused_on_import(client, raw):
    response = imported(client, "file.md", raw)
    assert response.status_code == 415
    detail = response.json()["detail"]
    assert detail["code"] == "not_utf8_text"
    assert detail["message"] == "file.md is not UTF-8 text. Only markdown or plain text files can be added."


def test_nul_in_json_content_is_refused(client):
    assert create(client, content="a\x00b").status_code == 415


def test_lone_surrogate_in_json_content_is_refused(client):
    response = client.post(
        "/api/intake/files",
        content=b'{"name": "x.md", "category": "misc_context", "content": "\\ud800"}',
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 415


# Read-only while a build runs (FR-B-8)


def start_fake_build(client):
    lab = client.app.state.lab
    lab.state.builds.append(Build(id="b-1", iteration=1))


def test_intake_is_read_only_while_a_build_runs(client):
    create(client, "notes.md")
    start_fake_build(client)
    attempts = [
        create(client, "more.md"),
        imported(client, "more.md", b"x"),
        client.patch("/api/intake/files/f-1", json={"content": "edit"}),
        client.delete("/api/intake/files/f-1"),
    ]
    for response in attempts:
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "intake_locked"
    assert client.get("/api/intake/files/f-1").json()["content"] == "text"


def test_reads_still_work_while_a_build_runs(client):
    create(client, "notes.md")
    start_fake_build(client)
    assert client.get("/api/intake/files").status_code == 200
    assert client.get("/api/state").json()["builds"][0]["status"] == "running"
