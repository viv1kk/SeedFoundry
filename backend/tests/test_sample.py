"""M4: the sample Seed (FR-DC-3, build-simulation.md §8). It is deterministic
(FR-DC-4, NFR-1), has every Ensemble section so Assay coverage can read 100%,
and has the sections D-36's feedback routing appends to in M10. The boundary
lint itself lands in M5; its zero findings on the sample are tested there."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from fastapi.testclient import TestClient

from seedfoundry.main import create_app
from seedfoundry.sample import SAMPLE_DIR, SAMPLE_FILES, sample_files
from test_no_em_dash import scanned_files

ROOT = Path(__file__).resolve().parents[2]
ENSEMBLE = (ROOT / "docs" / "ensemble" / "ensemble_context.md").read_text(encoding="utf-8")


def headings(text: str, level: int) -> list[str]:
    marks = "#" * level
    return [m.group(1).strip() for m in re.finditer(rf"^{marks} (.+)$", text, re.MULTILINE)]


def doc_part(number: int) -> str:
    """Section `## <number>.` of ensemble_context.md."""
    return re.search(rf"^## {number}\. .*?(?=^## |\Z)", ENSEMBLE, re.MULTILINE | re.DOTALL).group(0)


def ensemble_sections() -> dict[str, list[str]]:
    """Each core file's sections, as ensemble_context.md names them: the numbered
    #### headings for instrument awareness, environment and music, and the rows of
    the "What belongs here" table for person.md, which has no sub-headings."""
    belongs = re.search(r"### What belongs here\n(.*?)### What does NOT", doc_part(2), re.DOTALL).group(1)
    person = [row.split("|")[1].strip() for row in belongs.splitlines() if row.startswith("| ") and "---" not in row][1:]

    def numbered(number: int) -> list[str]:
        return [re.sub(r"^\d+\.\d+ ", "", h) for h in headings(doc_part(number), 4)]

    return {
        "person.md": person,
        "instrument-awareness.md": numbered(3),
        "environment.md": numbered(4),
        "music.md": numbered(5),
    }


def content(name: str) -> str:
    return dict((n, c) for n, _, c in sample_files())[name]


def load_once() -> tuple[list[dict], list[tuple[str, str, dict]]]:
    """Load the sample into a fresh lab; its files and its events without seq or wall_ts."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp, TestClient(create_app(Path(tmp))) as client:
        client.post("/api/demo/sample", json={})
        files = client.get("/api/intake/files").json()
        events = [(e.type, e.message, e.data) for e in client.app.state.lab.log.after(0)]
    return files, events


def test_every_sample_file_is_in_the_package():
    assert sorted(p.name for p in SAMPLE_DIR.glob("*.md")) == sorted(name for name, _ in SAMPLE_FILES)


def test_each_core_file_has_every_ensemble_section():
    sections = ensemble_sections()
    assert sections["person.md"][:3] == ["Domain expertise", "Subject matter knowledge", "Reasoning methods"]
    assert sections["environment.md"] == ["Data Layer", "User Experience", "Styling", "Adaptation Layer", "Protection Layer"]
    for name, expected in sections.items():
        found = [h.lower() for h in headings(content(name), 2)]
        assert found == [s.lower() for s in expected], name


def test_routing_targets_exist():
    # D-36: feedback is appended under named sections in M10. These are the ones the
    # demo's prefilled feedback is written to reach (build-simulation.md §9).
    assert {"Styling", "User Experience", "Data Layer", "Protection Layer"} <= set(headings(content("environment.md"), 2))
    assert "Decision Logic" in headings(content("music.md"), 2)
    assert "Reasoning methods" in headings(content("person.md"), 2)
    assert "Hallucination risks" in headings(content("instrument-awareness.md"), 3)


def test_files_are_one_to_two_screens():
    for name, _, text in sample_files():
        assert 1_000 < len(text.encode("utf-8")) < 9_000, name


def test_line_ends_are_normalised():
    for name, _, text in sample_files():
        assert "\r" not in text, name
        assert text.endswith("\n") and not text.endswith("\n\n"), name


def test_loading_the_sample_is_deterministic():
    # FR-DC-4, NFR-1: the same files, ids and content bytes, and the same events
    # (seq and wall_ts aside), every time.
    first, first_events = load_once()
    second, second_events = load_once()
    assert first == second
    assert first_events == second_events
    digests = [hashlib.sha256(f["content"].encode("utf-8")).hexdigest() for f in first]
    assert digests == [hashlib.sha256(c.encode("utf-8")).hexdigest() for _, _, c in sample_files()]


def test_reloading_changes_only_the_ids(client):
    client.post("/api/demo/sample", json={})
    first = client.get("/api/intake/files").json()
    client.post("/api/demo/sample", json={"replace": True})
    second = client.get("/api/intake/files").json()
    assert [f["id"] for f in second] == ["f-6", "f-7", "f-8", "f-9", "f-10"]
    strip = lambda files: [{k: v for k, v in f.items() if k != "id"} for f in files]  # noqa: E731
    assert strip(first) == strip(second)


def test_the_no_em_dash_scan_covers_the_sample():
    scanned = {p.relative_to(ROOT).as_posix() for p in scanned_files()}
    for name, _ in SAMPLE_FILES:
        assert f"backend/seedfoundry/sample/{name}" in scanned
