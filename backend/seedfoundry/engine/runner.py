"""The beat engine's runner (build-simulation.md §1, seed-reuse-notes.md §2.4, D-48).

start() writes the build's whole script at once (engine/script.py), saves the build
record with build.started, then plays the remaining beats on the server's event loop.
Each beat waits until the build's simulated progress reaches its sim_t; progress is
read from the clock and multiplied by the speed. Waits are cut into 50 ms slices, so a
change of speed or a skip acts within 50 ms. A skipped beat plays at once, with the
same events and sim_t as ever (FR-DC-4). Beats that are due together are saved in one
StateManager.apply, which changes how often the state is written, never what is in it.

One build at a time. stop() cancels the running build without touching the state;
Reset to start calls it before it removes the build (D-46).

The rebuild (FR-RB-4, FR-RB-5, D-67): start(2, feedback) saves the feedback as the Misc Context
file observer-feedback-iteration-1.md and starts iteration 2 in one state change, so a refusal or
a failed save leaves neither the file nor the build. Iteration 2's Update sub-steps carry the
routed files (D-36); each is written to intake when its beat plays, with intake.file_updated.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any

from seedfoundry.engine.catalogue import PHASES
from seedfoundry.engine.clock import Clock, RealClock
from seedfoundry.engine.script import Beat, BuildContext, script
from seedfoundry.intake import files as intake_files
from seedfoundry.intake.assay import inventory, missing_labels
from seedfoundry.intake.feedback import FEEDBACK_NAME, feedback_file
from seedfoundry.intake.files import IntakeError
from seedfoundry.events import Event
from seedfoundry.state import CATEGORY_LABELS, Build, Category, Emit, IntakeFile, State, StateManager

SLICE = 0.05
SPEEDS = (1, 2, 4)
EPSILON = 1e-9


class BuildError(IntakeError):
    """A build request the rules refuse; the API answers it like an intake error."""


class BuildEngine:
    def __init__(self, manager: StateManager, clock: Clock | None = None) -> None:
        self.manager = manager
        self.clock = clock or RealClock()
        self.speed = 1  # kept across builds and Reset (seed-reuse-notes.md §6.1); not saved
        self._task: asyncio.Task[None] | None = None
        self._beats: list[Beat] = []
        self._next = 0
        self._build_id = ""
        self._iteration = 1
        self._from_seq = 0
        self._progress = 0.0
        self._last = 0.0
        self._skip_phase: int | None = None
        self._skip_end = False

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    # Requests

    def start(self, iteration: int | None = None, feedback: str | None = None) -> Build:
        """Create a build for the current iteration and start playing it (FR-B-1). Moving to
        iteration 2 is the rebuild: it needs the observer feedback, which is saved with the build's
        start (FR-RB-3 to FR-RB-5, D-67)."""
        state = self.manager.state
        if state.build_running or self.running:
            raise BuildError(409, "build_running", "A build is running. Wait for it to finish, or use Reset to start.")
        target = self._target(state, iteration)
        rebuilding = target == 2 and state.iteration == 1
        if feedback is not None and not rebuilding:
            raise BuildError(409, "wrong_iteration", "Observer feedback starts iteration 2 from iteration 1's report; this Seed is past that.")
        if rebuilding and (feedback is None or not feedback.strip()):
            raise BuildError(422, "feedback_empty", "Start Rebuild needs observer feedback. Write what iteration 2 should change first.")
        missing = inventory(state.intake.files).missing
        if missing:
            raise BuildError(
                409,
                "core_files_missing",
                f"Start Build needs every core file. Missing: {missing_labels(missing)}.",
                missing=[c.value for c in missing],
            )
        files = list(state.intake.files)
        saved: IntakeFile | None = None
        if rebuilding:
            text = intake_files.check_text(FEEDBACK_NAME, feedback or "")
            existing = feedback_file(files)
            if existing is not None:
                saved = existing.model_copy(update={"content": text})
                files = [saved if f.id == existing.id else f for f in files]
            else:
                saved = IntakeFile(id=f"f-{state.next_file_id}", name=FEEDBACK_NAME, category=Category.MISC_CONTEXT, content=text)
                files.append(saved)
        prior = next((b for b in reversed(state.builds) if b.iteration == 1 and b.status == "completed"), None)
        context = BuildContext(f"b-{state.next_build_id}", target, files, prior=prior if target == 2 else None)
        beats = script(context)
        record = context.record()

        def begin(draft: State, emit: Emit) -> None:
            if saved is not None:
                _save_feedback(draft, emit, saved)
            replaced = [b.id for b in draft.builds if b.iteration == target]
            draft.builds = [b for b in draft.builds if b.iteration != target] + [record.model_copy(deep=True)]
            draft.iteration = target
            draft.next_build_id += 1
            beats[0].events[0]["data"]["replaces"] = replaced
            self._emit(draft, emit, beats[:1], record.id, target)

        self._from_seq = state.seq
        self.manager.apply(begin)
        self._beats, self._next = beats, 1
        self._build_id, self._iteration = record.id, target
        self._skip_phase, self._skip_end = None, False
        self._progress, self._last = 0.0, self.clock.now()
        self._task = asyncio.get_running_loop().create_task(self._play())
        return self.manager.state.build(record.id) or record

    def set_speed(self, speed: int) -> int:
        if speed not in SPEEDS:
            raise BuildError(422, "invalid_speed", "Speed is 1x, 2x or 4x.")
        if self.running:
            self._advance()
        self.speed = speed
        return speed

    def skip(self, to: str) -> dict[str, Any]:
        """Skip to the end of the current phase, or of the build. Pacing only."""
        if not self.running or self._next >= len(self._beats):
            raise BuildError(409, "no_build_running", "No build is running, so there is nothing to skip.")
        if to == "build":
            self._skip_end = True
            return {"skipping": "build"}
        index = self._beats[self._next].phase_index
        self._skip_phase = max(index, self._skip_phase if self._skip_phase is not None else -1)
        return {"skipping": "phase", "phase": PHASES[index].id, "name": PHASES[index].name}

    async def stop(self) -> None:
        """Cancel the running build, if any, and wait until it has stopped. The state is
        left as it is: the caller decides what happens to the build."""
        task, self._task = self._task, None
        if task is not None and not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    async def wait(self) -> None:
        """Until the running build finishes (tests)."""
        if self._task is not None:
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    # Iteration rules (D-49)

    @staticmethod
    def _target(state: State, iteration: int | None) -> int:
        if state.approval is not None:
            raise BuildError(409, "seed_approved", "This Seed is approved, so it is not built again. Use Reset to start a new one.")
        if iteration is None or iteration == state.iteration:
            return state.iteration
        if iteration == 2 and state.iteration == 1:
            if not any(b.iteration == 1 and b.status == "completed" for b in state.builds):
                raise BuildError(409, "iteration_1_not_built", "Iteration 2 needs a completed iteration 1 build.")
            return 2
        raise BuildError(409, "wrong_iteration", f"The current iteration is {state.iteration}.")

    # Playing

    def _emit(self, state: State, emit: Emit, beats: list[Beat], build_id: str, iteration: int) -> None:
        build = state.build(build_id)
        if build is None:
            raise asyncio.CancelledError  # removed by Reset; nothing more to play
        for beat in beats:
            for e in beat.events:
                if e["type"] == "phase.started":
                    build.phase = e["phase"]
                elif e["type"] == "build.completed":
                    build.status = "completed"
                emit(
                    type=e["type"],
                    level=e["level"],
                    message=e["message"],
                    code=e["code"],
                    data=e["data"],
                    phase=e.get("phase"),
                    step=e.get("step"),
                    build_id=build_id,
                    iteration=iteration,
                    sim_t=beat.sim_t,
                )
            for routed in beat.intake:
                _write_routed(state, emit, routed)

    def _apply(self, beats: list[Beat]) -> None:
        build_id, iteration, since = self._build_id, self._iteration, self._from_seq
        finishing = any(e["type"] == "build.completed" for beat in beats for e in beat.events)

        def keep_log(draft: State, events: list[Event]) -> None:
            # D-49: a finished build keeps its own events, exactly as they were streamed.
            earlier = [e for e in self.manager.log.after(since) if e.build_id == build_id]
            draft.build(build_id).log = earlier + [e for e in events if e.build_id == build_id]

        self.manager.apply(lambda draft, emit: self._emit(draft, emit, beats, build_id, iteration), keep_log if finishing else None)

    async def _play(self) -> None:
        try:
            while self._next < len(self._beats):
                await self._reach(self._beats[self._next])
                end = self._next + 1
                while end < len(self._beats) and self._ready(self._beats[end]):
                    end += 1
                batch, self._next = self._beats[self._next : end], end
                self._apply(batch)
                await asyncio.sleep(0)
        except asyncio.CancelledError:
            raise
        except Exception as error:  # a failed save: stop and free intake
            self._interrupt(f"{type(error).__name__}: {error}")

    def _advance(self) -> None:
        now = self.clock.now()
        self._progress += (now - self._last) * self.speed
        self._last = now

    def _covered(self, beat: Beat) -> bool:
        if self._skip_phase is not None and beat.phase_index > self._skip_phase:
            self._skip_phase = None
        return self._skip_end or (self._skip_phase is not None and beat.phase_index <= self._skip_phase)

    def _ready(self, beat: Beat) -> bool:
        """Due now, without waiting."""
        self._advance()
        if self._covered(beat):
            self._progress = max(self._progress, beat.sim_t)
            return True
        return beat.sim_t <= self._progress + EPSILON

    async def _reach(self, beat: Beat) -> None:
        while not self._ready(beat):
            await self.clock.sleep(min(SLICE, (beat.sim_t - self._progress) / self.speed))

    def _interrupt(self, reason: str) -> None:
        build_id = self._build_id

        def change(state: State, emit: Emit) -> None:
            build = state.build(build_id)
            if build is None or build.status != "running":
                return
            build.status = "interrupted"
            emit(
                type="build.interrupted",
                build_id=build_id,
                iteration=build.iteration,
                level="WARN",
                message=f"Build {build_id} stopped: {reason}. Start the build again.",
                data={"build_id": build_id, "reason": reason},
            )

        with contextlib.suppress(Exception):
            self.manager.apply(change)


def _save_feedback(state: State, emit: Emit, saved: IntakeFile) -> None:
    """Save the observer feedback as Misc Context (FR-RB-4, D-16): a new file, or the existing
    feedback file rewritten in place (D-67)."""
    label = CATEGORY_LABELS[Category.MISC_CONTEXT]
    existing = state.file(saved.id)
    if existing is None:
        state.intake.files.append(saved.model_copy())
        state.next_file_id += 1
        emit(
            type="intake.file_created",
            message=f"Created {saved.name} ({label}) from the rebuild",
            data={"file": saved.summary(), "source": "rebuild"},
        )
    elif existing.content != saved.content:
        existing.content = saved.content
        emit(
            type="intake.file_updated",
            message=f"{existing.name}: content saved ({existing.size:,} bytes) from the rebuild",
            data={"file": existing.summary(), "changed": ["content"], "source": "rebuild"},
        )


def _write_routed(state: State, emit: Emit, routed: IntakeFile) -> None:
    """Write one core file as the feedback routing left it (D-36). Intake is locked while the
    build runs, so the file is as the build read it; a file Reset removed is skipped."""
    file = state.file(routed.id)
    if file is None or file.content == routed.content:
        return
    file.content = routed.content
    emit(
        type="intake.file_updated",
        message=f"{file.name}: observer feedback added ({file.size:,} bytes)",
        data={"file": file.summary(), "changed": ["content"], "source": "feedback"},
    )
