"""Observer feedback as intake sees it (FR-RB-4, FR-RB-7): the Misc Context file the
rebuild saves, and its segments (paragraphs and list items). Routing segments into the
four core files is routing.py's (D-36, D-68).

Rejecting iteration n saves `observer-feedback-iteration-<n>.md` and starts iteration n + 1,
which routes that file (D-81). Earlier feedback files stay in Knowledge as they were."""

from __future__ import annotations

import re

from seedfoundry.state import Category, IntakeFile

_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_NAME = re.compile(r"^observer-feedback-iteration-\d+\.md$")


def feedback_name(rejected: int = 1) -> str:
    """The feedback file of the iteration it rejects."""
    return f"observer-feedback-iteration-{rejected}.md"


FEEDBACK_NAME = feedback_name(1)


def is_feedback(file: IntakeFile) -> bool:
    """Any iteration's observer feedback file."""
    return file.category == Category.MISC_CONTEXT and bool(_NAME.match(file.name))


def feedback_file(files: list[IntakeFile], rejected: int = 1) -> IntakeFile | None:
    name = feedback_name(rejected)
    return next((f for f in files if f.category == Category.MISC_CONTEXT and f.name == name), None)


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
