"""Single source of truth for intake, builds, iterations and approval, and its snapshot.

Every change goes through StateManager.apply: it runs on a copy of the state,
the copy is saved to var/ (D-3), and only then does it replace the live state
and its events go to the log. A change that raises, or a save that fails,
leaves the live state and the log as they were.
"""

from __future__ import annotations

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
    Category.PERSON: "Person",
    Category.INSTRUMENT_AWARENESS: "Instrument Awareness",
    Category.ENVIRONMENT: "Environment",
    Category.MUSIC: "Music",
    Category.MISC_CONTEXT: "Misc Context",
}

# One file each (FR-IN-3, D-4). Misc Context is unlimited.
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


class Build(BaseModel):
    """One run of the phase catalogue for one iteration. The engine fills it in from M5."""

    id: str
    iteration: int
    status: BuildStatus = "running"


class Approval(BaseModel):
    iteration: int


class State(BaseModel):
    schema_version: int = Field(default=SCHEMA, alias="schema")
    seq: int = 0
    iteration: int = 1
    next_file_id: int = 1
    intake: Intake = Intake()
    builds: list[Build] = []
    approval: Approval | None = None

    model_config = {"populate_by_name": True, "serialize_by_alias": True}

    @property
    def build_running(self) -> bool:
        return any(build.status == "running" for build in self.builds)

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
        return self.state.model_dump(mode="json")

    def apply(self, change: Callable[[State, Emit], T]) -> T:
        """Run a change on a copy of the state. The change calls emit(type=...,
        message=..., ...) once per event. Nothing is saved or published when it
        emits nothing."""
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
