"""Assay statistics over intake text (requirements §2, real): inventory, sizes,
Ensemble coverage per core file, the Seed name and the intake fingerprint.

Everything here is a pure function of the intake files, so the same intake
always gives the same figures (NFR-1).
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

from seedfoundry.state import CATEGORY_LABELS, CORE_CATEGORIES, Category, IntakeFile

# Each core file's Ensemble sections, as docs/ensemble/ensemble_context.md names them:
# the "What belongs here" categories for person.md, the numbered sub-headings for the
# other three. backend/tests/test_assay.py checks this table against that doc.
ENSEMBLE_SECTIONS: dict[Category, tuple[str, ...]] = {
    Category.PERSON: (
        "Domain expertise",
        "Subject matter knowledge",
        "Reasoning methods",
        "Analytical approaches",
        "Decision-making patterns",
        "Problem-solving strategies",
        "Thinking frameworks",
    ),
    Category.INSTRUMENT_AWARENESS: ("Context Management", "Model Behaviour", "Execution Constraints"),
    Category.ENVIRONMENT: ("Data Layer", "User Experience", "Styling", "Adaptation Layer", "Protection Layer"),
    Category.MUSIC: ("Purpose", "Core Principles", "Value Logic", "Decision Logic"),
}

UNTITLED = "Untitled Seed"

_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_FENCE = re.compile(r"^\s*(```|~~~)")
_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\S")


def filled(file: IntakeFile) -> bool:
    """A file with something other than whitespace (D-42 (a)): the checklist's rule and T-01's."""
    return bool(file.content.strip())


def key(title: str) -> str:
    """A heading compared without case, extra spaces or a trailing colon."""
    return " ".join(title.strip().rstrip(":").split()).casefold()


@dataclass
class Section:
    level: int
    title: str
    line: int  # 1-based line of the heading
    body: list[str] = field(default_factory=list)  # lines up to the next heading of any level


def sections(text: str) -> list[Section]:
    """Headings in document order with the lines under each. Lines inside a code fence are
    never headings. Text before the first heading is dropped."""
    found: list[Section] = []
    fenced = False
    for number, line in enumerate(text.split("\n"), start=1):
        if _FENCE.match(line):
            fenced = not fenced
        match = None if fenced else _HEADING.match(line)
        if match:
            found.append(Section(len(match.group(1)), match.group(2).strip(), number))
        elif found:
            found[-1].body.append(line)
    return found


def section_lines(text: str, title: str, level: int = 2) -> list[str] | None:
    """The lines of a `level` heading named `title`, sub-headings and their lines included,
    or None when the file has no such heading."""
    parts = sections(text)
    for index, part in enumerate(parts):
        if part.level == level and key(part.title) == key(title):
            lines = list(part.body)
            for sub in parts[index + 1 :]:
                if sub.level <= level:
                    break
                lines += [f"{'#' * sub.level} {sub.title}", *sub.body]
            return lines
    return None


def statements(lines: list[str]) -> int:
    """List items in a block of lines; a block with no list counts its paragraphs."""
    items = sum(1 for line in lines if _ITEM.match(line))
    if items:
        return items
    paragraphs, inside = 0, False
    for line in lines:
        text = line.strip()
        starts = bool(text) and not text.startswith("#")
        paragraphs += starts and not inside
        inside = starts
    return paragraphs


def seed_name(music: IntakeFile | None) -> str:
    """The first heading of music.md, else "Untitled Seed" (OQ-7)."""
    parts = sections(music.content) if music else []
    return parts[0].title if parts else UNTITLED


def digest(files: list[IntakeFile]) -> str:
    """sha256 of the intake content: every file's category, name and content, in Ensemble
    order then by name, so file ids and the order files were added do not matter."""
    order = {category: index for index, category in enumerate(Category)}
    rows = sorted(([f.category.value, f.name, f.content] for f in files), key=lambda r: (order[Category(r[0])], r[1], r[2]))
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def fingerprint(files: list[IntakeFile]) -> str:
    """The short form shown in logs and generated files."""
    return digest(files)[:6]


@dataclass
class Coverage:
    file: IntakeFile
    expected: tuple[str, ...]
    found: list[str]
    missing: list[str]

    @property
    def percent(self) -> int:
        return round(100 * len(self.found) / len(self.expected)) if self.expected else 100


def coverage(file: IntakeFile) -> Coverage:
    """Which of the file's Ensemble sections it has as `##` headings."""
    expected = ENSEMBLE_SECTIONS[file.category]
    present = {key(s.title) for s in sections(file.content) if s.level == 2}
    found = [name for name in expected if key(name) in present]
    return Coverage(file, expected, found, [name for name in expected if key(name) not in present])


@dataclass
class Inventory:
    core: list[IntakeFile]  # in Ensemble order
    context: list[IntakeFile]  # Misc Context, in intake order
    missing: list[Category]  # core slots with no filled file

    @property
    def total_bytes(self) -> int:
        return sum(f.size for f in self.core + self.context)


def inventory(files: list[IntakeFile]) -> Inventory:
    by_category = {f.category: f for f in files if f.category in CORE_CATEGORIES}
    core = [by_category[c] for c in CORE_CATEGORIES if c in by_category and filled(by_category[c])]
    missing = [c for c in CORE_CATEGORIES if c not in by_category or not filled(by_category[c])]
    return Inventory(core, [f for f in files if f.category == Category.MISC_CONTEXT], missing)


def missing_labels(missing: list[Category]) -> str:
    return ", ".join(CATEGORY_LABELS[c] for c in missing)


def kilobytes(size: int) -> str:
    return f"{size / 1024:.1f} KB"
