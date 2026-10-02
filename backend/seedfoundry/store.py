"""JSON persistence under var/, written atomically (D-3).

A document is written to a temporary file in the same folder, flushed to disk,
then renamed over the old one, so a crash leaves either the old document or
the new one and never half of either.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any


class StoreError(RuntimeError):
    """The stored document exists but cannot be read."""


class JsonStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> Any | None:
        """The stored document, or None when nothing has been saved yet."""
        try:
            text = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError as error:
            raise StoreError(
                f"{self.path} is not valid JSON ({error}). Move it aside to start with an empty lab."
            ) from error

    def save(self, document: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(document, ensure_ascii=False, indent=2)
        handle, temp = tempfile.mkstemp(dir=self.path.parent, prefix=self.path.stem + "-", suffix=".tmp")
        try:
            with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as file:
                file.write(text)
                file.flush()
                os.fsync(file.fileno())
            _replace(temp, self.path)
        except BaseException:
            Path(temp).unlink(missing_ok=True)
            raise


def _replace(source: str, target: Path, attempts: int = 10) -> None:
    # On Windows a reader (indexer, antivirus, an editor) can hold the target
    # open for a moment, which makes the rename fail. Retry briefly.
    for attempt in range(attempts):
        try:
            os.replace(source, target)
            return
        except PermissionError:
            if attempt == attempts - 1:
                raise
            time.sleep(0.05)
