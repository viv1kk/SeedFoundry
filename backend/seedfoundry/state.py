"""Single source of truth for intake, builds, iterations and approval, and its snapshot.

Every change goes through StateManager.apply: it runs on a copy of the state,
the copy is saved to var/ (D-3), and only then does it replace the live state
and its events go to the log. A change that raises, or a save that fails,
leaves the live state and the log as they were.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal, TypeVar

from pydantic import BaseModel, Field, computed_field

from seedfoundry.events import Event, EventLog, wall_now
from seedfoundry.store import JsonStore

SCHEMA = 1
STATE_FILE = "state.json"


class Category(StrEnum):
    """Intake categories, in Ensemble order (FR-IN-2). Screen labels are in CATEGORY_LABELS."""

    PERSON = "person"
    INSTRUMENT_AWARENESS = "instrument_awareness"
    ENVIRONMENT = "environment"
    MUSIC = "music"
    MISC_CONTEXT = "misc_context"


CATEGORY_LABELS = {
    Category.PERSON: "Identity.md",
    Category.INSTRUMENT_AWARENESS: "Tools_and_Skills.md",
    Category.ENVIRONMENT: "Environment.md",
    Category.MUSIC: "Value.md",
    Category.MISC_CONTEXT: "Misc Context",
}

# The four initiation files are the only files the Knowledge page offers (D-84). Misc Context
# stays as a code term for the observer feedback file, which is kept with the builds and never
# listed on Knowledge.

# The name a file gets when it is added to a core category on screen (D-85). A name ending in
# "_<digits>.md" is versioned: each iteration whose feedback changes the file steps the number up
# (Environment_01.md, then Environment_02.md), keeping its width.
CORE_FILE_NAMES = {
    Category.PERSON: "Identity.md",
    Category.INSTRUMENT_AWARENESS: "Tools_and_Skills.md",
    Category.ENVIRONMENT: "Environment_01.md",
    Category.MUSIC: "Value_0001.md",
}

# The Seed file shown beside each initiation file on the Knowledge page: a high-level picture
# only, stated by the stakeholder (D-86), not the generation mapping (build-simulation.md §7).
CATEGORY_SEED_FILES = {
    Category.PERSON: None,
    Category.INSTRUMENT_AWARENESS: "protection.md",
    Category.ENVIRONMENT: "adaptation.md",
    Category.MUSIC: "core.md",
}

_VERSIONED = re.compile(r"^(.*_)(\d+)(\.md)$", re.IGNORECASE)


def next_version(name: str) -> str:
    """The name of a versioned file's next version, or the name as it is when it has no number."""
    found = _VERSIONED.match(name)
    if found is None:
        return name
    digits = found.group(2)
    return f"{found.group(1)}{int(digits) + 1:0{len(digits)}d}{found.group(3)}"

# One line each, for the Knowledge page's empty state (ui-spec.md §2), from the Ensemble
# one-line summaries in docs/ensemble/ensemble_context.md.
CATEGORY_DESCRIPTIONS = {
    Category.PERSON: "Who does the work: how the AI thinks, reasons and decides.",
    Category.INSTRUMENT_AWARENESS: "Which tool it uses: how the AI works with the model, its context and its limits.",
    Category.ENVIRONMENT: "Where the work happens: data, user experience, styling, adaptation and protection.",
    Category.MUSIC: "Why the work exists: purpose, principles, value logic and decisions.",
    Category.MISC_CONTEXT: "Anything else worth knowing. Optional, and any number of files.",
}

# One file each (FR-IN-3, D-4). Misc Context, the observer feedback only since D-84, is unlimited.
CORE_CATEGORIES = (Category.PERSON, Category.INSTRUMENT_AWARENESS, Category.ENVIRONMENT, Category.MUSIC)


class IntakeFile(BaseModel):
    id: str
    name: str
    category: Category
    content: str = ""

    @computed_field
    @property
    def size(self) -> int:
        """Content size in UTF-8 bytes."""
        return len(self.content.encode("utf-8"))

    def summary(self) -> dict[str, Any]:
        """The file without its content, as intake events carry it (D-32)."""
        return {"id": self.id, "name": self.name, "category": self.category.value, "size": self.size}


class Intake(BaseModel):
    files: list[IntakeFile] = []


BuildStatus = Literal["running", "completed", "interrupted"]


class PlanItem(BaseModel):
    id: str
    name: str


class PhasePlan(BaseModel):
    """One phase of a build as planned at its start (build-simulation.md §2)."""

    id: str
    name: str
    weight: int
    steps: list[PlanItem] = []
    tests: list[PlanItem] = []


class Build(BaseModel):
    """One run of the phase catalogue for one iteration (D-49). The engine creates it with
    build.started, sets `phase` at each phase.started, and on build.completed sets the status
    and keeps the build's events in `log`, which the snapshot leaves out. `files` keeps the
    intake the build read, as it read it (D-36, D-67): iteration 1's versions of the files stay
    with build 1, and build 2 keeps the routed files and the feedback it built from. The snapshot
    leaves them out too; GET /api/builds/{id}/files serves them."""

    id: str
    iteration: int
    status: BuildStatus = "running"
    seed_name: str = ""
    fingerprint: str = ""
    phase: str | None = None
    plan: list[PhasePlan] = []
    # The simulated length of the whole build, so the Build page reads progress from sim_t (D-54).
    # 0 on a record saved before M6.
    sim_seconds: float = 0.0
    files: list[IntakeFile] = []
    log: list[Event] = []

    def summary(self) -> dict[str, Any]:
        """The record without its log and files, as build.started carries it and the snapshot shows it."""
        return self.model_dump(mode="json", exclude={"log", "files"})


class Approval(BaseModel):
    """The approved Seed (FR-F-1, D-73): which completed build it is. `approved_at` is the wall-clock
    time of the approval, kept like an event's wall_ts: the Seed page shows its date, and no file,
    zip or compared value holds it (NFR-1, OQ-33)."""

    iteration: int
    build_id: str = ""
    approved_at: str | None = None


class State(BaseModel):
    schema_version: int = Field(default=SCHEMA, alias="schema")
    seq: int = 0
    iteration: int = 1
    next_file_id: int = 1
    next_build_id: int = 1
    intake: Intake = Intake()
    builds: list[Build] = []
    approval: Approval | None = None

    model_config = {"populate_by_name": True, "serialize_by_alias": True}

    @property
    def build_running(self) -> bool:
        return any(build.status == "running" for build in self.builds)

    def build(self, build_id: str) -> Build | None:
        return next((b for b in self.builds if b.id == build_id), None)

    def file(self, file_id: str) -> IntakeFile | None:
        return next((f for f in self.intake.files if f.id == file_id), None)

    def core_file(self, category: Category) -> IntakeFile | None:
        if category not in CORE_CATEGORIES:
            return None
        return next((f for f in self.intake.files if f.category == category), None)


T = TypeVar("T")
Emit = Callable[..., None]


class StateManager:
    def __init__(self, store: JsonStore, state: State) -> None:
        self.store = store
        self.state = state
        self.log = EventLog(base=state.seq)

    @classmethod
    def open(cls, var_dir: Path) -> StateManager:
        """Load the saved state, or start empty. A build that was running when
        the server stopped cannot resume, so it is marked interrupted (D-33)."""
        store = JsonStore(var_dir / STATE_FILE)
        saved = store.load()
        manager = cls(store, State.model_validate(saved) if saved is not None else State())
        if manager.state.build_running:
            manager.apply(_interrupt_running_builds)
        return manager

    def snapshot(self) -> dict[str, Any]:
        """The state without build logs and kept files, which GET /api/builds/{id}/events and
        /files serve (D-49, D-67)."""
        return self.state.model_dump(mode="json", exclude={"builds": {"__all__": {"log", "files"}}})

    def apply(self, change: Callable[[State, Emit], T], then: Callable[[State, list[Event]], None] | None = None) -> T:
        """Run a change on a copy of the state. The change calls emit(type=...,
        message=..., ...) once per event. Nothing is saved or published when it
        emits nothing. `then` sees the copy and the numbered events before the
        save, for a change that keeps its own events (a finished build's log)."""
        draft = self.state.model_copy(deep=True)
        pending: list[dict[str, Any]] = []
        result = change(draft, lambda **fields: pending.append(fields))
        if not pending:
            return result
        events = []
        for fields in pending:
            draft.seq += 1
            fields.setdefault("iteration", draft.iteration)
            events.append(Event(seq=draft.seq, wall_ts=wall_now(), **fields))
        if then is not None:
            then(draft, events)
        self.store.save(draft.model_dump(mode="json"))
        self.state = draft
        self.log.extend(events)
        return result


def _interrupt_running_builds(state: State, emit: Emit) -> None:
    for build in state.builds:
        if build.status == "running":
            build.status = "interrupted"
            emit(
                type="build.interrupted",
                build_id=build.id,
                iteration=build.iteration,
                level="WARN",
                message=f"Build {build.id} stopped when the server restarted. Start the build again.",
                data={"build_id": build.id},
            )
