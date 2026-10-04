"""The approved Seed (`seed_package`, requirements §5): Approve, its three files and their zip, and
the Seed page's data (FR-F-1 to FR-F-5, FR-R-4, ui-spec.md §7, D-73 to D-75).

Approve records which completed build is the Seed. Everything else is computed on request from that
build's kept files and log, and the earlier iterations' builds, as the report is (D-64), so it reads
the same after a restart, and the same approval always gives the same files, zip bytes and page data
(NFR-1). The one exception is `approved_at`, the wall-clock time of the approval: the page shows its
date, and nothing else holds it (OQ-33).

The files are the layers Synthesis drafted and planted (generate/layers.py, D-72), byte for byte,
plus a Known issues section in each when the approved build has open findings (FR-F-4, D-10):
iteration 1's every finding; boundary advisories never (D-12, OQ-31).
"""

from __future__ import annotations

import hashlib
import io
import re
import zipfile
from typing import Any

from seedfoundry import report
from seedfoundry.engine.runner import earlier_builds
from seedfoundry.events import wall_now
from seedfoundry.generate import layers
from seedfoundry.intake import assay
from seedfoundry.intake.files import IntakeError
from seedfoundry.state import Approval, Build, Category, Emit, IntakeFile, State

# Every zip entry carries this time, the earliest a zip can hold, so the bytes never follow the clock.
ZIP_TIME = (1980, 1, 1, 0, 0, 0)
ZIP_URL = "/api/seed/zip"


def file_url(name: str) -> str:
    return f"/api/seed/files/{name}"


# Approve


def prior_build(state: State, build: Build) -> Build | None:
    """The previous iteration's completed build, which "Changes since" reads (D-81)."""
    earlier = earlier_builds(state, build.iteration)
    return earlier[-1] if earlier and earlier[-1].iteration == build.iteration - 1 else None


def approve(build_id: str):
    """A change that approves a completed build as the Seed (FR-F-1, D-73). Only the current
    iteration's build can be approved, once, with no build running; Reset clears it (D-46)."""

    def change(state: State, emit: Emit) -> Approval:
        if state.approval is not None:
            raise IntakeError(
                409,
                "seed_approved",
                f"This Seed is already approved at iteration {state.approval.iteration}. Use Reset to start a new one.",
            )
        build = state.build(build_id)
        if build is None:
            raise IntakeError(404, "build_not_found", f"No build with id {build_id}.")
        if state.build_running:
            raise IntakeError(409, "build_running", "A build is running. Approve once it has finished.")
        if build.status != "completed" or not build.log:
            raise IntakeError(409, "report_not_ready", f"Build {build_id} has not completed, so there is nothing to approve.")
        if build.iteration != state.iteration:
            raise IntakeError(
                409,
                "iteration_superseded",
                f"Iteration {build.iteration + 1} was rebuilt from this build, so iteration {state.iteration} is the one to approve.",
            )
        made = seed_files(build, earlier_builds(state, build.iteration))
        issues = [f["id"] for f in report.raised(build)]
        state.approval = Approval(iteration=build.iteration, build_id=build.id, approved_at=wall_now())
        known = f"{len(issues)} known {'issue' if len(issues) == 1 else 'issues'}" if issues else "no known issues"
        emit(
            type="seed.approved",
            message=f'Seed approved: "{build.seed_name}", iteration {build.iteration}; 3 files, {known}',
            data={
                "iteration": build.iteration,
                "build_id": build.id,
                "seed_name": build.seed_name,
                "files": [{"name": name, "bytes": len(text.encode("utf-8")), "sha256": digest(text)} for name, text in made.items()],
                "known_issues": issues,
            },
        )
        return state.approval

    return change


def approved(state: State) -> tuple[Build, list[Build]]:
    """The approved build and every earlier iteration's, oldest first, or 404 seed_not_approved."""
    build = state.build(state.approval.build_id) if state.approval is not None else None
    if build is None:
        raise IntakeError(404, "seed_not_approved", "No Seed is approved yet. Approve a completed build from its report first.")
    return build, earlier_builds(state, build.iteration)


# The files and the zip


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def seed_files(build: Build, earlier: list[Build]) -> dict[str, str]:
    """core.md, adaptation.md and protection.md: the build's drafts, regenerated from its kept files
    exactly as Synthesis made them (the learned rules from the earlier builds' findings), with Known
    issues when the build has open findings."""
    learned = [{**f, "iteration": b.iteration} for b in earlier for f in report.raised(b)]
    made = layers.drafts(build.files, build.seed_name, build.iteration, build.fingerprint, learned)
    issues = report.raised(build)
    if issues:
        made = {name: layers.with_known_issues(text, issues, build.iteration) for name, text in made.items()}
    return made


def zip_bytes(files: dict[str, str]) -> bytes:
    """The three files in one zip, in layer order, stored, with fixed times and attributes: the same
    files always give the same bytes (D-74)."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, text in files.items():
            entry = zipfile.ZipInfo(name, date_time=ZIP_TIME)
            entry.compress_type = zipfile.ZIP_STORED
            entry.create_system = 3  # the same on every platform
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, text.encode("utf-8"))
    return buffer.getvalue()


def zip_name(seed: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", seed.casefold()).strip("-") or "seed"
    return f"{slug}-seed.zip"


# The Seed page (ui-spec.md §7)


def music_file(files: list[IntakeFile]) -> IntakeFile | None:
    return next((f for f in assay.inventory(files).core if f.category == Category.MUSIC), None)


def purpose(files: list[IntakeFile]) -> dict[str, str]:
    """What this Seed does: the Purpose section, else the first paragraph (ui-spec.md §7). As the
    files are, a mention of an intake file reads as the layer that holds it."""
    music = music_file(files)
    if music is None:
        return {"from": "none", "text": ""}
    rewrite = layers.Source(files).rewrite
    lines = layers.trim(assay.section_lines(music.content, "Purpose") or [])
    if any(line.strip() for line in lines):
        return {"from": "purpose", "text": rewrite("\n".join(lines))}
    paragraph: list[str] = []
    for line in music.content.split("\n"):
        if line.strip() and not layers.heading(line):
            paragraph.append(line)
        elif paragraph:
            break
    return {"from": "first_paragraph", "text": rewrite("\n".join(paragraph))} if paragraph else {"from": "none", "text": ""}


def tests_by_phase(built: dict[str, Any]) -> list[dict[str, Any]]:
    names = {t["id"]: t["name"] for t in built["tests"]}
    return [
        {
            "id": phase["id"],
            "index": phase["index"],
            "name": phase["name"],
            "result": phase["result"],
            "findings": phase["findings"],
            "tests": [{"id": test_id, "name": names.get(test_id, ""), "status": status} for test_id, status in phase["tests"].items()],
        }
        for phase in built["phases"]
    ]


def history(build: Build, reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Each iteration up to the approved one, with the observer feedback that rejected it between it
    and the next, from the reports and their "Changes since" (OQ-9, OQ-30, D-81). `reports` are the
    iterations' reports, oldest first, ending with the approved build's."""
    items: list[dict[str, Any]] = []
    for built in reports:
        changes = built.get("changes")
        if changes:
            routed = sorted({n for update in changes["updates"] for n in update["segments"]})
            items.append(
                {
                    "kind": "feedback",
                    "rejected": built["iteration"] - 1,
                    "name": changes["feedback"]["name"] if changes["feedback"] else "",
                    "content": changes["feedback"]["content"] if changes["feedback"] else "",
                    "segments": changes["feedback"]["segments"] if changes["feedback"] else 0,
                    "routed": len(routed),
                    "files_updated": len({update["file"] for update in changes["updates"]}),
                }
            )
        item: dict[str, Any] = {
            "kind": "iteration",
            "iteration": built["iteration"],
            "build_id": built["build_id"],
            "verdict": built["verdict"],
            "findings": built["counts"]["findings"],
            "approved": built["build_id"] == build.id,
        }
        if changes:
            item.update(resolved=changes["resolved"], open=changes["open"], prior_findings=len(changes["findings"]))
        items.append(item)
    return items


def page(state: State) -> dict[str, Any]:
    """The Seed page's data: everything ui-spec.md §7 shows, with the three files' text for Preview."""
    build, earlier = approved(state)
    chain = [*earlier, build]
    reports = [
        report.assemble(b, chain[i - 1] if i and chain[i - 1].iteration == b.iteration - 1 else None)
        for i, b in enumerate(chain)
    ]
    built = reports[-1]
    made = seed_files(build, earlier)
    approval = state.approval
    return {
        "seed_name": build.seed_name,
        "fingerprint": build.fingerprint,
        "approval": {"iteration": build.iteration, "build_id": build.id, "approved_at": approval.approved_at if approval else None},
        "purpose": purpose(build.files),
        "verdict": built["verdict"],
        "counts": built["counts"],
        "phases": tests_by_phase(built),
        "history": history(build, reports),
        "known_issues": [
            {k: f.get(k) for k in ("id", "category", "severity", "panel_titles", "message", "expected", "shown")}
            for f in report.raised(build)
        ],
        "files": [
            {
                "name": name,
                "title": layers.layer(name).title,
                "description": layers.description(name, build.iteration),
                "bytes": len(text.encode("utf-8")),
                "sha256": digest(text),
                "content": text,
                "url": file_url(name),
            }
            for name, text in made.items()
        ],
        "zip": {"name": zip_name(build.seed_name), "bytes": len(zip_bytes(made)), "url": ZIP_URL},
    }
