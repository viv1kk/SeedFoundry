"""Intake files: create, rename, change category, update content, delete, import.

Rules enforced here, whichever client calls:
- FR-IN-3: one file each for the four core categories. A second one is
  refused unless the request says replace, which deletes the existing file.
- FR-IN-11: at most 1 MB (1,048,576 bytes) of UTF-8 text per file (D-34).
- FR-B-8: intake is read-only while a build runs.

Each function is a change for StateManager.apply.
"""

from __future__ import annotations

from pathlib import PurePath

from seedfoundry.state import CATEGORY_LABELS, Category, Emit, IntakeFile, State

MAX_FILE_BYTES = 1024 * 1024
MAX_NAME_LENGTH = 120

# FR-IN-7: filename to pre-selected category on import. Anything else is Misc Context.
FILENAME_HINTS = {
    "person.md": Category.PERSON,
    "player.md": Category.PERSON,
    "instrument-awareness.md": Category.INSTRUMENT_AWARENESS,
    "instrument_awareness.md": Category.INSTRUMENT_AWARENESS,
    "environment.md": Category.ENVIRONMENT,
    "music.md": Category.MUSIC,
}


class IntakeError(Exception):
    """A request the intake rules refuse. The API turns it into an error response."""

    def __init__(self, status: int, code: str, message: str, **extra: object) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.extra = extra


def suggest_category(filename: str) -> Category:
    return FILENAME_HINTS.get(PurePath(filename).name.lower(), Category.MISC_CONTEXT)


def check_name(name: str) -> str:
    name = name.strip()
    if not name:
        raise IntakeError(422, "invalid_name", "A file needs a name.")
    if len(name) > MAX_NAME_LENGTH:
        raise IntakeError(422, "invalid_name", f"File names are limited to {MAX_NAME_LENGTH} characters.")
    if "/" in name or "\\" in name:
        raise IntakeError(422, "invalid_name", "A file name cannot contain / or \\.")
    return name


def normalise(text: str) -> str:
    # Browsers hand back textarea content with \n line ends, so store it that
    # way from the start. Otherwise the first autosave after an import would
    # rewrite every line end of an untouched file.
    return text.replace("\r\n", "\n").replace("\r", "\n")


def check_text(name: str, text: str) -> str:
    """Content sent as JSON text: size and text-only checks, then normalised line ends."""
    try:
        size = len(text.encode("utf-8"))
    except UnicodeEncodeError:
        raise _not_text(name) from None
    if size > MAX_FILE_BYTES:
        raise _too_large(name, size)
    if "\x00" in text:
        raise _not_text(name)
    return normalise(text)


def decode_upload(name: str, raw: bytes) -> str:
    """Bytes from an imported file: size, strict UTF-8 and text-only checks."""
    if len(raw) > MAX_FILE_BYTES:
        raise _too_large(name, len(raw))
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise _not_text(name) from None
    if "\x00" in text:
        raise _not_text(name)
    return normalise(text)


def _too_large(name: str, size: int) -> IntakeError:
    return IntakeError(
        413,
        "file_too_large",
        f"{name} is {size:,} bytes. Files are limited to 1 MB ({MAX_FILE_BYTES:,} bytes).",
        limit_bytes=MAX_FILE_BYTES,
        size_bytes=size,
    )


def _not_text(name: str) -> IntakeError:
    return IntakeError(415, "not_utf8_text", f"{name} is not UTF-8 text. Only markdown or plain text files can be added.")


def _check_unlocked(state: State) -> None:
    if state.build_running:
        raise IntakeError(409, "intake_locked", "Knowledge files are read-only while a build runs.")


def _get(state: State, file_id: str) -> IntakeFile:
    found = state.file(file_id)
    if found is None:
        raise IntakeError(404, "file_not_found", f"No file with id {file_id}.")
    return found


def _claim_slot(state: State, emit: Emit, category: Category, replace: bool, newcomer: str, keep_id: str | None = None) -> None:
    """Make room in a core slot, or refuse (FR-IN-3)."""
    existing = state.core_file(category)
    if existing is None or existing.id == keep_id:
        return
    label = CATEGORY_LABELS[category]
    if not replace:
        raise IntakeError(
            409,
            "core_slot_taken",
            f"{label} already has {existing.name}. Replace it with {newcomer}?",
            existing=existing.summary(),
        )
    state.intake.files.remove(existing)
    emit(
        type="intake.file_deleted",
        message=f"Deleted {existing.name} ({label}), replaced by {newcomer}",
        data={"file": existing.summary(), "replaced_by": newcomer},
    )


def create(name: str, category: Category, content: str = "", replace: bool = False, source: str = "new"):
    """A change that adds a file. Returns the new file."""

    def change(state: State, emit: Emit) -> IntakeFile:
        _check_unlocked(state)
        clean_name = check_name(name)
        text = content if source == "import" else check_text(clean_name, content)
        _claim_slot(state, emit, category, replace, clean_name)
        file = IntakeFile(id=f"f-{state.next_file_id}", name=clean_name, category=category, content=text)
        state.next_file_id += 1
        state.intake.files.append(file)
        verb = "Imported" if source == "import" else "Created"
        emit(
            type="intake.file_created",
            message=f"{verb} {file.name} ({CATEGORY_LABELS[category]})",
            data={"file": file.summary(), "source": source},
        )
        return file

    return change


def import_upload(filename: str, raw: bytes, category: Category | None = None, replace: bool = False):
    """A change that imports one uploaded .md file (FR-IN-7, FR-IN-11)."""
    name = check_name(PurePath(filename.replace("\\", "/")).name)
    if not name.lower().endswith(".md"):
        raise IntakeError(415, "not_markdown", f"{name} is not a .md file. Import accepts markdown files only.")
    text = decode_upload(name, raw)
    return create(name, category or suggest_category(name), text, replace, source="import")


def update(file_id: str, name: str | None = None, category: Category | None = None, content: str | None = None, replace: bool = False):
    """A change that renames, recategorises or rewrites a file. No event when nothing changes."""

    def change(state: State, emit: Emit) -> IntakeFile:
        _check_unlocked(state)
        file = _get(state, file_id)
        new_name = file.name if name is None else check_name(name)
        new_content = file.content if content is None else check_text(new_name, content)
        new_category = file.category if category is None else category
        changed = [
            field
            for field, before, after in (
                ("name", file.name, new_name),
                ("category", file.category, new_category),
                ("content", file.content, new_content),
            )
            if before != after
        ]
        if not changed:
            return file
        if "category" in changed:
            _claim_slot(state, emit, new_category, replace, new_name, keep_id=file.id)
        old_name = file.name
        file.name, file.category, file.content = new_name, new_category, new_content
        parts = []
        if "name" in changed:
            parts.append(f"renamed {old_name} to {new_name}")
        if "category" in changed:
            parts.append(f"moved to {CATEGORY_LABELS[new_category]}")
        if "content" in changed:
            parts.append(f"content saved ({file.size:,} bytes)")
        emit(
            type="intake.file_updated",
            message=f"{old_name}: {', '.join(parts)}",
            data={"file": file.summary(), "changed": changed},
        )
        return file

    return change


def delete(file_id: str):
    def change(state: State, emit: Emit) -> None:
        _check_unlocked(state)
        file = _get(state, file_id)
        state.intake.files.remove(file)
        emit(
            type="intake.file_deleted",
            message=f"Deleted {file.name} ({CATEGORY_LABELS[file.category]})",
            data={"file": file.summary()},
        )

    return change
