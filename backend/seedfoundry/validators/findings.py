"""From validator problems to findings (FR-T-6, FR-T-7, D-14, D-63).

A validator reports problems (problems.py); it never names a defect. Here problems are grouped into
findings by what found them: the test, the check and the panel. Each catalogue entry below says
which problems are its own, so the mapping reads the validators' output and never the overlay's
list of patches (dashboard/overlay.py), which this module does not import. Several problems make
one finding: N-1 alone is eighteen problems at All products (seventeen bars and their sum).

A problem that fits no catalogue entry (a user's own Seed could raise one; the sample never does)
still becomes a finding, never a silent pass: problems of one test, check and panel are one
finding, numbered after its category's letter as N-X1, V-X1, L-X1 in the order they are first
found, so a catalogue id is never reused for something it does not describe.

Each finding carries its id, category, test, panel and panels (with their titles), the expected and
shown values of its headline problem, severity, the phase and sub-step that find it, a message
built from the problems' own figures, and every problem behind it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from seedfoundry.validators.problems import Problem


@dataclass(frozen=True)
class Defect:
    """A catalogue entry (build-simulation.md §5, seed-reuse-notes.md §5.8) and the problems that are its own."""

    id: str
    category: str
    test: str
    panels: frozenset[str] = frozenset()  # empty: any panel
    checks: frozenset[str] = frozenset()  # empty: any check

    def owns(self, problem: Problem) -> bool:
        return (
            problem.test == self.test
            and (not self.panels or problem.panel in self.panels)
            and (not self.checks or problem.check in self.checks)
        )


def _numeric(defect_id: str, panel: str) -> Defect:
    return Defect(defect_id, "Numeric", "T-16", panels=frozenset({panel}))


def _visual(defect_id: str, test: str, *checks: str) -> Defect:
    return Defect(defect_id, "Visual", test, checks=frozenset(checks))


CATALOGUE: tuple[Defect, ...] = (
    _numeric("N-1", "entitlement"),  # part sums against the KPI
    _numeric("N-2", "seats-treemap"),  # percentage set sums to 100
    _numeric("N-3", "k-recoverable"),  # derived KPI against its formula and the cost panel
    _numeric("N-4", "seats"),  # table total against its row sums
    _numeric("N-5", "candidates"),  # table total against its row sums
    _visual("V-1", "T-17", "pie-slices", "categorical-bar"),
    _visual("V-2", "T-19", "red-for-faults"),
    _visual("V-3", "T-19", "palette", "class-colour"),
    _visual("V-4", "T-18", "format", "currency"),
    _visual("V-5", "T-18", "axis-label", "axis-unit"),
    _visual("V-6", "T-19", "grid", "overflow", "truncation"),
    _visual("V-7", "T-19", "font"),
    _visual("V-8", "T-20", "contrast"),
    Defect("L-1", "Latency", "T-15", checks=frozenset({"latency"})),
)
CATALOGUE_IDS = tuple(d.id for d in CATALOGUE)


def order(finding_id: str) -> int:
    """Where a finding sorts: catalogue ids in catalogue order, any other after them (use a stable
    sort, so those keep the order they were found in)."""
    return CATALOGUE_IDS.index(finding_id) if finding_id in CATALOGUE_IDS else len(CATALOGUE_IDS)

CATEGORIES = ("Numeric", "Visual", "Latency")
CATEGORY_OF_TEST = {"T-15": "Latency", "T-16": "Numeric", "T-17": "Visual", "T-18": "Visual", "T-19": "Visual", "T-20": "Visual"}
LETTER = {"Numeric": "N", "Visual": "V", "Latency": "L"}
# A wrong figure misleads the reader, so it is high; a visual or latency defect is medium (OQ-26).
SEVERITY = {"Numeric": "high", "Visual": "medium", "Latency": "medium"}
# Where each test runs (build-simulation.md §2): its phase and sub-step.
WHERE = {
    "T-15": ("probe", "probe.latency"),
    "T-16": ("harvest", "harvest.numeric"),
    "T-17": ("harvest", "harvest.chart"),
    "T-18": ("harvest", "harvest.visual"),
    "T-19": ("harvest", "harvest.visual"),
    "T-20": ("harvest", "harvest.contrast"),
}
# The problem a numeric finding leads with: a sum or a total before a single figure.
HEADLINE = ("part-sum", "percent-sum", "table-total", "kpi-formula", "cross-panel")
DASHBOARD = "Dashboard"


@dataclass
class Finding:
    id: str
    category: str
    test: str
    catalogued: bool
    problems: list[Problem] = field(default_factory=list)
    titles: dict[str, str] = field(default_factory=dict)

    @property
    def severity(self) -> str:
        return SEVERITY[self.category]

    @property
    def phase(self) -> str:
        return WHERE[self.test][0]

    @property
    def step(self) -> str:
        return WHERE[self.test][1]

    @property
    def panels(self) -> list[str]:
        return list(dict.fromkeys(p.panel for p in self.problems))

    @property
    def headline(self) -> Problem:
        for check in HEADLINE if self.category == "Numeric" else ():
            first = next((p for p in self.problems if p.check == check), None)
            if first is not None:
                return first
        return self.problems[0]

    @property
    def message(self) -> str:
        """The headline problem's own message, and how many problems stand behind it."""
        count, panels = len(self.problems), len(self.panels)
        more = "" if count == 1 else f"; {count} problems in all" if panels == 1 else f"; {count} problems on {panels} panels"
        return f"{self.headline.message}{more}"

    def as_data(self) -> dict[str, Any]:
        head = self.headline
        return {
            "id": self.id,
            "category": self.category,
            "test": self.test,
            "checks": list(dict.fromkeys(p.check for p in self.problems)),
            "panel": self.panels[0],
            "panels": self.panels,
            "panel_titles": [self.titles.get(p, DASHBOARD) for p in self.panels],
            "expected": head.expected_text,
            "shown": head.shown_text,
            "severity": self.severity,
            "phase": self.phase,
            "step": self.step,
            "message": self.message,
            "catalogued": self.catalogued,
            "advisory": False,
            "problems": [p.as_data() for p in self.problems],
        }


def assign(problems: list[Problem], titles: dict[str, str]) -> list[Finding]:
    """The findings these problems make: catalogue entries first, in catalogue order, then any
    problems no entry owns, one finding per test, check and panel, in the order first found."""
    found: dict[str, Finding] = {}
    others: dict[tuple[str, str, str], Finding] = {}
    numbered = {letter: 0 for letter in LETTER.values()}
    for problem in problems:
        defect = next((d for d in CATALOGUE if d.owns(problem)), None)
        if defect is not None:
            found.setdefault(defect.id, Finding(defect.id, defect.category, defect.test, True, titles=titles)).problems.append(problem)
            continue
        key = (problem.test, problem.check, problem.panel)
        if key not in others:
            category = CATEGORY_OF_TEST[problem.test]
            numbered[LETTER[category]] += 1
            others[key] = Finding(f"{LETTER[category]}-X{numbered[LETTER[category]]}", category, problem.test, False, titles=titles)
        others[key].problems.append(problem)
    ordered = [found[d.id] for d in CATALOGUE if d.id in found]
    return ordered + list(others.values())
