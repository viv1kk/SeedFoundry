"""FastAPI app. Every route is under /api.

Routes are async so every change to the state runs on the one event loop,
which also serves the SSE streams.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, Header, Query, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from seedfoundry import dashboard, demo, events
from seedfoundry.config import var_dir
from seedfoundry.data import DATASETS, dataset
from seedfoundry.engine.clock import Clock
from seedfoundry.engine.runner import BuildEngine
from seedfoundry.intake import files
from seedfoundry.state import (
    CATEGORY_DESCRIPTIONS,
    CATEGORY_LABELS,
    CORE_CATEGORIES,
    Category,
    IntakeFile,
    StateManager,
)


class NewFile(BaseModel):
    name: str
    category: Category
    content: str = ""
    replace: bool = False


class LoadSample(BaseModel):
    replace: bool = False


class StartBuild(BaseModel):
    # Omitted: the current iteration (FR-B-1). 2 starts iteration 2 after a completed
    # iteration 1, until M10's rebuild does it with the feedback (D-49).
    iteration: Literal[1, 2] | None = None


class SetSpeed(BaseModel):
    speed: Literal[1, 2, 4]


class Skip(BaseModel):
    to: Literal["phase", "build"]


class FileChanges(BaseModel):
    name: str | None = None
    category: Category | None = None
    content: str | None = None
    replace: bool = False


def create_app(data_dir: Path | None = None, clock: Clock | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.lab = StateManager.open(data_dir or var_dir())
        app.state.engine = BuildEngine(app.state.lab, clock)
        for name in DATASETS:
            dataset(name)  # generated once, at start, so the first dashboard is quick (NFR-3)
        yield
        # A build cannot outlive the server: it stays "running" on disk and is marked
        # interrupted at the next start (D-33).
        await app.state.engine.stop()

    app = FastAPI(title="SeedFoundry", lifespan=lifespan)

    @app.exception_handler(files.IntakeError)
    async def intake_error(request: Request, error: files.IntakeError) -> JSONResponse:
        return JSONResponse(
            status_code=error.status,
            content={"detail": {"code": error.code, "message": error.message, **error.extra}},
        )

    @app.exception_handler(dashboard.QueryError)
    async def query_error(request: Request, error: dashboard.QueryError) -> JSONResponse:
        return JSONResponse(status_code=error.status, content={"detail": {"code": error.code, "message": error.message}})

    def lab(request: Request) -> StateManager:
        return request.app.state.lab

    def engine(request: Request) -> BuildEngine:
        return request.app.state.engine

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        """Readiness, which run.py polls before announcing the app."""
        return {"status": "ok", "app": "SeedFoundry"}

    @app.get("/api/state")
    async def state(request: Request) -> dict[str, Any]:
        """The full snapshot, current as of its seq."""
        return lab(request).snapshot()

    @app.get("/api/events")
    async def event_stream(
        request: Request,
        after: int = Query(0, ge=0),
        last_event_id: str | None = Header(None),
    ) -> StreamingResponse:
        """SSE: replay events after a seq, then follow. A browser reconnecting
        sends Last-Event-ID, which wins over ?after= because it is newer."""
        if last_event_id is not None and last_event_id.strip().isdigit():
            after = int(last_event_id)
        manager = lab(request)
        return StreamingResponse(
            events.stream(manager.log, after, manager.state.iteration),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/api/intake/categories")
    async def categories() -> dict[str, Any]:
        """Categories in Ensemble order with their screen labels and one-line descriptions,
        and the filename hints import uses (FR-IN-7)."""
        return {
            "categories": [
                {
                    "id": c.value,
                    "label": CATEGORY_LABELS[c],
                    "core": c in CORE_CATEGORIES,
                    "description": CATEGORY_DESCRIPTIONS[c],
                }
                for c in Category
            ],
            "filename_hints": {name: c.value for name, c in files.FILENAME_HINTS.items()},
            "max_file_bytes": files.MAX_FILE_BYTES,
        }

    @app.get("/api/intake/files")
    async def list_files(request: Request) -> list[IntakeFile]:
        return lab(request).state.intake.files

    @app.post("/api/intake/files", status_code=201)
    async def create_file(request: Request, body: NewFile) -> IntakeFile:
        return lab(request).apply(files.create(body.name, body.category, body.content, body.replace))

    @app.post("/api/intake/import", status_code=201)
    async def import_file(
        request: Request,
        filename: str = Query(..., min_length=1),
        category: Category | None = Query(None),
        replace: bool = Query(False),
    ) -> IntakeFile:
        """Import one file. The body is the file's raw bytes, so the UTF-8 check
        sees exactly what is on disk. Category defaults to the filename hint."""
        raw = await request.body()
        return lab(request).apply(files.import_upload(filename, raw, category, replace))

    @app.get("/api/intake/files/{file_id}")
    async def read_file(request: Request, file_id: str) -> IntakeFile:
        found = lab(request).state.file(file_id)
        if found is None:
            raise files.IntakeError(404, "file_not_found", f"No file with id {file_id}.")
        return found

    @app.patch("/api/intake/files/{file_id}")
    async def update_file(request: Request, file_id: str, body: FileChanges) -> IntakeFile:
        return lab(request).apply(files.update(file_id, body.name, body.category, body.content, body.replace))

    @app.delete("/api/intake/files/{file_id}", status_code=204)
    async def delete_file(request: Request, file_id: str) -> Response:
        lab(request).apply(files.delete(file_id))
        return Response(status_code=204)

    # Builds (FR-B-1, D-49)

    @app.post("/api/builds", status_code=201)
    async def start_build(request: Request, body: StartBuild | None = None) -> dict[str, Any]:
        """Start a build of the current iteration. 409 while a build runs or a core file is missing."""
        return engine(request).start(body.iteration if body else None).summary()

    @app.get("/api/builds/{build_id}/events")
    async def build_events(request: Request, build_id: str) -> dict[str, Any]:
        """A build's events in order: the kept log of a finished build, or what the
        in-memory log holds of a running or interrupted one (D-49)."""
        manager = lab(request)
        build = manager.state.build(build_id)
        if build is None:
            raise files.IntakeError(404, "build_not_found", f"No build with id {build_id}.")
        events = build.log or [e for e in manager.log.after(0) if e.build_id == build_id]
        return {"build_id": build_id, "status": build.status, "seq": manager.state.seq, "events": events}

    # Dashboard and datasets (FR-D-1 to FR-D-6, D-56). The query engine runs here: every figure
    # is aggregated from the seat rows at request time, and the frontend only renders.

    def known_dashboard(dashboard_id: str) -> None:
        if dashboard_id != dashboard.DASHBOARD_ID:
            raise dashboard.QueryError(404, "dashboard_not_found", f"No dashboard {dashboard_id!r}.")

    def known_dataset(name: str) -> None:
        if name not in DATASETS:
            raise dashboard.QueryError(404, "dataset_not_found", f"No dataset {name!r}. Datasets: {', '.join(DATASETS)}.")

    @app.get("/api/dashboards/{dashboard_id}")
    async def get_dashboard(
        dashboard_id: str,
        iteration: int = Query(..., ge=1, le=2),
        dataset_name: str = Query(dashboard.DEFAULT_DATASET, alias="dataset"),
        drill: str = Query(""),
        page: int = Query(1, ge=1),
        sort: str | None = Query(None),
        direction: str | None = Query(None),
    ) -> dict[str, Any]:
        """The descriptor and the payload at one drill level (`drill`: steps joined by "/", a
        step's levels by "."). 404 drill_not_found for a path the data does not have."""
        known_dashboard(dashboard_id)
        known_dataset(dataset_name)
        return dashboard.dashboard(iteration, dataset_name, drill or None, page, sort, direction)

    @app.get("/api/dashboards/{dashboard_id}/descriptor")
    async def get_descriptor(dashboard_id: str, iteration: int = Query(..., ge=1, le=2)) -> dict[str, Any]:
        known_dashboard(dashboard_id)
        return dashboard.descriptor(iteration)

    @app.get("/api/datasets")
    async def list_datasets() -> list[dict[str, Any]]:
        return [dataset(name).summary() for name in DATASETS]

    @app.get("/api/datasets/{name}")
    async def get_dataset(name: str) -> dict[str, Any]:
        """Every product and seat row, usage included, for inspection."""
        known_dataset(name)
        return dataset(name).rows()

    # Demo controller (D-46). The client asks before replacing or clearing; the server
    # applies the same intake rules as for the user's own changes.

    @app.post("/api/demo/sample", status_code=201)
    async def load_sample(request: Request, body: LoadSample) -> list[IntakeFile]:
        """Load sample Seed. 409 intake_not_empty unless intake is empty or `replace` is set."""
        return lab(request).apply(demo.load_sample(body.replace))

    @app.post("/api/demo/clear")
    async def clear_intake(request: Request) -> dict[str, int]:
        """Clear intake: delete every file."""
        return {"deleted": lab(request).apply(demo.clear_intake())}

    @app.post("/api/demo/reset")
    async def reset(request: Request) -> dict[str, int]:
        """Reset to start: no files, no builds, iteration 1. Allowed while a build runs:
        the engine is stopped first, so no beat lands after the reset."""
        await engine(request).stop()
        return lab(request).apply(demo.reset())

    @app.get("/api/demo/speed")
    async def get_speed(request: Request) -> dict[str, int]:
        """The build speed, held by the engine and not saved (D-48)."""
        return {"speed": engine(request).speed}

    @app.post("/api/demo/speed")
    async def set_speed(request: Request, body: SetSpeed) -> dict[str, int]:
        """Speed 1x, 2x or 4x: pacing only (FR-DC-4). Kept across builds and Reset; emits no event."""
        return {"speed": engine(request).set_speed(body.speed)}

    @app.post("/api/demo/skip")
    async def skip(request: Request, body: Skip) -> dict[str, Any]:
        """Skip to the end of the phase or the build: pacing only. 409 when no build runs."""
        return engine(request).skip(body.to)

    return app


app = create_app()
