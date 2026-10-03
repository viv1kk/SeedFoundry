"""FastAPI app. Every route is under /api.

Routes are async so every change to the state runs on the one event loop,
which also serves the SSE streams.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, Query, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from seedfoundry import events
from seedfoundry.config import var_dir
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


class FileChanges(BaseModel):
    name: str | None = None
    category: Category | None = None
    content: str | None = None
    replace: bool = False


def create_app(data_dir: Path | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.lab = StateManager.open(data_dir or var_dir())
        yield

    app = FastAPI(title="SeedFoundry", lifespan=lifespan)

    @app.exception_handler(files.IntakeError)
    async def intake_error(request: Request, error: files.IntakeError) -> JSONResponse:
        return JSONResponse(
            status_code=error.status,
            content={"detail": {"code": error.code, "message": error.message, **error.extra}},
        )

    def lab(request: Request) -> StateManager:
        return request.app.state.lab

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

    return app


app = create_app()
