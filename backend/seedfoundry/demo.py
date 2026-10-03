"""Demo controller actions that change the state (FR-DC-2, ui-spec.md §8, D-46).

Load sample Seed and Clear intake are intake changes under the user's rules:
refused with 409 intake_locked while a build runs (FR-B-8), and they emit the
normal intake events, so every client follows them. Reset to start returns the
lab to a fresh start and is allowed at any time, build or not.

Each function is a change for StateManager.apply.
"""

from __future__ import annotations

from typing import Any

from seedfoundry.intake import files
from seedfoundry.sample import sample_files
from seedfoundry.state import CATEGORY_LABELS, Emit, IntakeFile, State


def _plural(count: int, word: str) -> str:
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def load_sample(replace: bool = False):
    """A change that fills intake with the sample Seed. Intake must be empty
    unless `replace` is set, which deletes every file first, Misc Context
    included (OQ-17). Returns the new files."""

    def change(state: State, emit: Emit) -> list[IntakeFile]:
        files.check_unlocked(state)
        count = len(state.intake.files)
        if count and not replace:
            raise files.IntakeError(
                409,
                "intake_not_empty",
                f"Knowledge has {_plural(count, 'file')}. Loading the sample Seed replaces them all.",
                files=count,
            )
        for file in list(state.intake.files):
            files.delete(file.id)(state, emit)
        return [files.create(name, category, content, source="sample")(state, emit) for name, category, content in sample_files()]

    return change


def clear_intake():
    """A change that deletes every intake file. Returns how many it deleted."""

    def change(state: State, emit: Emit) -> int:
        files.check_unlocked(state)
        removed = list(state.intake.files)
        for file in removed:
            files.delete(file.id)(state, emit)
        return len(removed)

    return change


def reset():
    """A change back to a fresh start: no files, no builds, no approval,
    iteration 1. The seq and the file id counter carry on, so an id is never
    reused and the event log stays one sequence. Speed and theme live in the
    browser and are kept. Nothing to reset emits nothing."""

    def change(state: State, emit: Emit) -> dict[str, Any]:
        removed = list(state.intake.files)
        builds = len(state.builds)
        if not removed and not builds and state.approval is None and state.iteration == 1:
            return {"files_removed": 0, "builds_removed": 0}
        for file in removed:
            state.intake.files.remove(file)
            emit(
                type="intake.file_deleted",
                message=f"Deleted {file.name} ({CATEGORY_LABELS[file.category]})",
                data={"file": file.summary()},
            )
        state.builds = []
        state.approval = None
        state.iteration = 1
        summary = {"files_removed": len(removed), "builds_removed": builds}
        emit(
            type="demo.reset",
            message=f"Reset to start: {_plural(len(removed), 'file')} and {_plural(builds, 'build')} removed",
            data=summary,
        )
        return summary

    return change
