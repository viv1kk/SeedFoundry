"""Observer feedback routed into the four core files (FR-RB-7, A-4, D-36).

The feedback is split into segments (paragraphs and list items, feedback.py). Each segment is
scored against the routing targets below, which are the boundary lint's own rule sets
(boundary.py, build-simulation.md §6.1) grouped by the section they name as a concern's home,
plus a few words for each home the lint has no rule for (person.md's reasoning, music.md's
value). A segment's score for a target is the number of the target's patterns it matches. The
highest score wins, and a tie goes to the target listed first: environment.md Styling, User
Experience, Data Layer and Protection Layer, then instrument-awareness.md, person.md and
music.md, D-36's fixed order. A segment that matches nothing stays in the feedback file only.

Each routed segment is appended verbatim at the end of its `##` section, under
`### Observer feedback (iteration 1)`, which is created if the section lacks it; a missing
section is created at the end of the file. A segment already under that heading is not added
again, so routing the same feedback twice changes nothing the second time.

Everything here is a pure function of the intake files, so the same intake and feedback always
give the same edits (NFR-1). The build logs the routing as an LLMClient decision (simulated):
no model is asked, these rules decide.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from seedfoundry.intake import assay, boundary
from seedfoundry.intake.feedback import feedback_file, segments
from seedfoundry.state import CORE_CATEGORIES, Category, IntakeFile

HEADING = "Observer feedback (iteration 1)"


@dataclass(frozen=True)
class Target:
    category: Category
    section: str
    patterns: tuple[re.Pattern[str], ...]

    @property
    def home(self) -> str:
        return f"{assay.CATEGORY_LABELS[self.category]}, {self.section}"


def _lint(home: str) -> tuple[re.Pattern[str], ...]:
    """The boundary lint's patterns whose suggested home is `home`."""
    return tuple(p.regex for rule in boundary.RULES for p in rule.patterns if p.home == home)


def _words(*expressions: str) -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(e, re.IGNORECASE) for e in expressions)


# D-36's fixed order. Styling and layout, chart choice, then data and totals, then checks and
# guardrails, then the model, then reasoning and evidence, then priorities, decisions and value.
TARGETS: tuple[Target, ...] = (
    Target(
        Category.ENVIRONMENT,
        "Styling",
        _lint(boundary.STYLING)
        + _words(
            r"\bpies?\b",
            r"\bslices?\b",
            r"\baxis\b|\baxes\b",
            r"\bnumber formats?\b|\bformat(?:s|ted|ting)?\b",
            r"\bthousands separators?\b",
            r"\$ sign\b|\bdollar sign\b|\bcurrency\b",
            r"\bcontrast\b",
            r"\bserif\b",
            r"\bgutters?\b|\bgrid\b|\bmisaligned\b|\balign(?:ed|ment)?\b",
            r"\boverflow\w*|\btruncat\w*|\bclipped\b|\bcut off\b",
            r"\blegend\b",
            r"\b(?:red|green|amber|orange|blue|teal|grey|gray)\b",
        ),
    ),
    Target(
        Category.ENVIRONMENT,
        "User Experience",
        _lint(boundary.UX)
        + _words(
            r"\bpanels?\b",
            r"\bdrill\w*",
            r"\bbreadcrumbs?\b",
            r"\bspinner\b",
            r"\bloading\b|\bslow\w*",
            r"\blatency\b",
            r"\bwait\w*",
            r"\bseconds?\b",
            r"\bsort\w*",
        ),
    ),
    Target(
        Category.ENVIRONMENT,
        "Data Layer",
        _lint(boundary.DATA)
        + _words(
            r"\btotals?\b",
            r"\bsums?\b|\bsummed\b|\badd(?:s|ed)? up\b",
            r"\brecount\w*|\brecomput\w*|\breconcil\w*",
            r"\bfigures?\b",
            r"\brecords?\b|\brows?\b",
            r"\btwice\b|\bdouble[- ]counted\b|\bduplicat\w*",
            r"\bpercentages?\b|\bshares?\b",
            r"\bdatasets?\b|\bthe data\b",
        ),
    ),
    Target(
        Category.ENVIRONMENT,
        "Protection Layer",
        _lint(boundary.PROTECTION)
        + _words(
            r"\bchecks?\b|\bchecked\b",
            r"\bvalidat\w*",
            r"\bverif\w*",
            r"\bread[- ]only\b",
            r"\bexports?\b",
            r"\bsandbox\b",
            r"\bprobes?\b",
        ),
    ),
    Target(
        Category.INSTRUMENT_AWARENESS,
        "Model Behaviour",
        _lint(boundary.MODEL) + _words(r"\barithmetic\b", r"\bcontext\b"),
    ),
    Target(
        Category.PERSON,
        "Reasoning methods",
        _words(
            r"\breason\w*",
            r"\bevidence\b",
            r"\bassum\w*",
            r"\binfer\w*",
            r"\bconclu\w*",
            r"\bclaims?\b",
        ),
    ),
    Target(Category.MUSIC, "Core Principles", _lint(boundary.PRINCIPLES)),
    Target(
        Category.MUSIC,
        "Decision Logic",
        _lint(boundary.DECISIONS) + _words(r"\bdecid\w*|\bdecisions?\b", r"\bchoices?\b|\bchoos\w*", r"\bprefer\w*"),
    ),
    Target(
        Category.MUSIC,
        "Value Logic",
        _words(r"\bvalue\b", r"\bsavings?\b|\bsaves?\b", r"\bsuccess\w*", r"\btrade-?offs?\b", r"\bworth\b", r"\bspend\b"),
    ),
)


@dataclass(frozen=True)
class Placement:
    """Where one segment goes, and why: the words of the winning target it matched."""

    number: int  # 1-based, in the feedback's order
    text: str
    target: Target | None
    matched: tuple[str, ...]


@dataclass
class SectionChange:
    section: str  # the heading as the file has it, or as created
    segments: list[int] = field(default_factory=list)  # appended
    present: list[int] = field(default_factory=list)  # already under the heading, not added again
    lines_added: int = 0
    created: bool = False  # the `##` section was missing and was added


@dataclass
class FileChange:
    before: IntakeFile
    after: IntakeFile
    sections: list[SectionChange]

    @property
    def lines_added(self) -> int:
        return sum(s.lines_added for s in self.sections)

    @property
    def changed(self) -> bool:
        return self.after.content != self.before.content


@dataclass
class Routing:
    feedback: IntakeFile | None
    placements: list[Placement]
    changes: dict[Category, FileChange]  # each core file the intake has
    files: list[IntakeFile]  # every intake file after routing, in intake order

    @property
    def routed(self) -> list[Placement]:
        return [p for p in self.placements if p.target is not None]

    @property
    def kept(self) -> list[Placement]:
        return [p for p in self.placements if p.target is None]


def score(text: str) -> list[tuple[Target, int, tuple[str, ...]]]:
    """Each target with how many of its patterns the segment matches, and the words they matched,
    in the order they appear in the text. Allowlisted phrases (Seed v0.1's panel titles) are not
    words."""
    cleaned = boundary.clean(text)
    found = []
    for target in TARGETS:
        hits = sorted((m for m in (p.search(cleaned) for p in target.patterns) if m), key=lambda m: m.start())
        words: list[str] = []
        for hit in hits:
            if hit.group(0).casefold() not in {w.casefold() for w in words}:
                words.append(hit.group(0))
        found.append((target, len(hits), tuple(words)))
    return found


def place(number: int, text: str) -> Placement:
    """The target with the most matching patterns; the first listed wins a tie (D-36)."""
    best: tuple[Target, int, tuple[str, ...]] | None = None
    for candidate in score(text):
        if candidate[1] and (best is None or candidate[1] > best[1]):
            best = candidate
    return Placement(number, text, best[0], best[2]) if best else Placement(number, text, None, ())


def _bounds(content: str, length: int, section: str) -> tuple[int, int] | None:
    """The 0-based line of the `##` heading named `section`, and the line where its section ends."""
    heads = [(s.line - 1, s.level, s.title) for s in assay.sections(content)]
    start = next((i for i, level, title in heads if level == 2 and assay.key(title) == assay.key(section)), None)
    if start is None:
        return None
    return start, next((i for i, level, _ in heads if i > start and level <= 2), length)


def _append(content: str, section: str, texts: list[tuple[int, str]]) -> tuple[str, SectionChange]:
    """Append each (number, segment) under the section's feedback heading, verbatim."""
    lines = content.split("\n")
    change = SectionChange(section)
    bounds = _bounds(content, len(lines), section)
    if bounds is None:
        change.created = True
        at = len(lines)
        while at > 0 and not lines[at - 1].strip():
            at -= 1
        block = ["", f"## {section}", "", f"### {HEADING}"]
        for number, text in texts:
            block += ["", *text.split("\n")]
            change.segments.append(number)
        lines[at:at] = block
        change.lines_added = len(block)
        return "\n".join(lines), change

    start, end = bounds
    heads = [(s.line - 1, s.level, s.title) for s in assay.sections(content) if start <= s.line - 1 < end]
    change.section = heads[0][2]
    own = next((i for i, level, title in heads if level == 3 and assay.key(title) == assay.key(HEADING)), None)
    stop = end if own is None else next((i for i, level, _ in heads if i > own and level <= 3), end)
    existing = "\n".join(lines[own + 1 : stop]) if own is not None else ""
    floor = own if own is not None else start
    at = stop
    while at > floor + 1 and not lines[at - 1].strip():
        at -= 1
    block = [] if own is not None else ["", f"### {HEADING}"]
    for number, text in texts:
        if own is not None and text in existing:
            change.present.append(number)
            continue
        block += ["", *text.split("\n")]
        change.segments.append(number)
    if not change.segments:
        return content, change
    if at < len(lines) and lines[at].strip():
        block.append("")  # keep a blank line before the heading that follows
    lines[at:at] = block
    change.lines_added = len(block)
    return "\n".join(lines), change


def route(files: list[IntakeFile]) -> Routing:
    """Route the feedback file's segments into the core files. Without a feedback file, or with
    one that has no segment, nothing changes."""
    feedback = feedback_file(files)
    placements = [place(n, text) for n, text in enumerate(segments(feedback.content), start=1)] if feedback else []
    core = {f.category: f for f in files if f.category in CORE_CATEGORIES}
    changes: dict[Category, FileChange] = {}
    for category in CORE_CATEGORIES:
        if category not in core:
            continue
        before = core[category]
        content = before.content
        sections: list[SectionChange] = []
        for target in TARGETS:
            if target.category != category:
                continue
            texts = [(p.number, p.text) for p in placements if p.target is target]
            if texts:
                content, change = _append(content, target.section, texts)
                sections.append(change)
        changes[category] = FileChange(before, before.model_copy(update={"content": content}), sections)
    after = {change.after.id: change.after for change in changes.values()}
    return Routing(feedback, placements, changes, [after.get(f.id, f) for f in files])
