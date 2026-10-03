"""Observer feedback as intake sees it (FR-RB-4, FR-RB-7): the Misc Context file the
rebuild saves, and its segments (paragraphs and list items). Routing segments into the
four core files is M10's (D-36); until then iteration 2 reads the feedback and routes
nothing (D-52)."""

from __future__ import annotations

import re

from seedfoundry.state import Category, IntakeFile

FEEDBACK_NAME = "observer-feedback-iteration-1.md"

_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")


def feedback_file(files: list[IntakeFile]) -> IntakeFile | None:
    return next((f for f in files if f.category == Category.MISC_CONTEXT and f.name == FEEDBACK_NAME), None)


def segments(text: str) -> list[str]:
    """Paragraphs and list items, in order, each as written. Headings are not segments."""
    found: list[str] = []
    current: list[str] = []

    def close() -> None:
        if current:
            found.append("\n".join(current).strip())
            current.clear()

    for line in text.split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            close()
        elif _ITEM.match(line):
            close()
            current.append(line)
        else:
            current.append(line)
    close()
    return [segment for segment in found if segment]
