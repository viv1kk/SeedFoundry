"""Ensemble boundary check (T-03, build-simulation.md §6.1, FR-T-1): a rule-based lint
over the four core files, from the boundary table in docs/ensemble/ensemble_context.md §6.

Each rule names the files it checks and a set of patterns, each with the section the
matched content belongs in. A line gets at most one finding per rule: the first pattern
that matches. Findings are advisories (D-12): they are reported with file, line and
suggested home, and never change the verdict.

Misc Context files are not checked: the boundary table is about the four core files,
and context (vendor notes, observer feedback) has no single home by design (D-50).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from seedfoundry.state import CATEGORY_LABELS, Category, IntakeFile

# Homes are named by the category's screen name (D-84): the file itself may be Environment_02.md.
ENV = CATEGORY_LABELS[Category.ENVIRONMENT]
IA = CATEGORY_LABELS[Category.INSTRUMENT_AWARENESS]
MUSIC = CATEGORY_LABELS[Category.MUSIC]
PERSON = CATEGORY_LABELS[Category.PERSON]

# Phrases that look like a rule's keyword but are not that concern: Seed v0.1's panel
# titles, which environment.md's User Experience layer names (M4 self-review).
ALLOWLIST = (
    re.compile(r"\boptimi[sz]ation candidates\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class Pattern:
    regex: re.Pattern[str]
    home: str  # suggested home: "<file>, <section>"


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    checks: tuple[Category, ...]
    patterns: tuple[Pattern, ...]


def _p(expression: str, home: str, flags: int = re.IGNORECASE) -> Pattern:
    return Pattern(re.compile(expression, flags), home)


DATA = f"{ENV}, Data Layer"
PROTECTION = f"{ENV}, Protection Layer"
STYLING = f"{ENV}, Styling"
UX = f"{ENV}, User Experience"
MODEL = f"{IA}, Model Behaviour or Execution Constraints"
PRINCIPLES = f"{MUSIC}, Core Principles"
DECISIONS = f"{MUSIC}, Decision Logic"

RULES: tuple[Rule, ...] = (
    Rule(
        "B-DATA",
        f"Data mappings, schemas, columns, file paths or raw records outside {ENV}",
        (Category.PERSON, Category.INSTRUMENT_AWARENESS, Category.MUSIC),
        (
            _p(r"\bschemas?\b", DATA),
            _p(r"\bcolumns?\b", DATA),
            _p(r"\bdata (?:mappings?|fields?|types?|sources?|model)\b", DATA),
            _p(r"\bfield (?:names?|lists?|mappings?)\b", DATA),
            _p(r"\b(?:primary|foreign) keys?\b", DATA),
            _p(r"\bselect\b.+\bfrom\b", DATA),
            _p(r"\b[\w-]+\.(?:csv|tsv|xlsx?|json|parquet|sql|db)\b", DATA),
            _p(r"(?:\b[a-z]:\\|(?<![\w/.])/[\w.-]+/[\w./-]+)", DATA),
            _p(r"`[a-z][a-z0-9]*_[a-z0-9_]+`", DATA, 0),
            _p(r"\b[A-Z]{2,5}-\d{4,}\b", DATA, 0),
        ),
    ),
    Rule(
        "B-SEC",
        f"Security, access or guardrail language in {PERSON} or {MUSIC}",
        (Category.PERSON, Category.MUSIC),
        (
            _p(r"\bsecurity\b", PROTECTION),
            _p(r"\baccess (?:control|rights?|rules?|levels?|management|policy|policies)\b", PROTECTION),
            _p(r"\bguardrails?\b", PROTECTION),
            _p(r"\bpermissions?\b", PROTECTION),
            _p(r"\bcredentials?\b", PROTECTION),
            _p(r"\bpasswords?\b", PROTECTION),
            _p(r"\bprivacy\b", PROTECTION),
            _p(r"\bPII\b", PROTECTION, 0),
            _p(r"\bencrypt\w*", PROTECTION),
            _p(r"\bauthenticat\w*", PROTECTION),
            _p(r"\bauthori[sz]ation\b", PROTECTION),
            _p(r"\bsafety rules?\b", PROTECTION),
            _p(r"\bconfidential\w*", PROTECTION),
        ),
    ),
    Rule(
        "B-UI",
        f"Colours, themes, layouts or navigation outside {ENV}",
        (Category.PERSON, Category.INSTRUMENT_AWARENESS, Category.MUSIC),
        (
            _p(r"\bcolou?rs?\b", STYLING),
            _p(r"\bthemes?\b", STYLING),
            _p(r"\bpalettes?\b", STYLING),
            _p(r"\bfonts?\b|\btypefaces?\b", STYLING),
            _p(r"(?<![\w&])#[0-9a-f]{6}\b|(?<![\w&])#[0-9a-f]{3}\b", STYLING),
            _p(r"\b(?:dark|light) mode\b", STYLING),
            _p(r"\bcss\b", STYLING),
            _p(r"\b(?:pie|bar|line) charts?\b|\bcharts?\b", STYLING),
            _p(r"\blayouts?\b", UX),
            _p(r"\bnavigat\w*", UX),
            _p(r"\bscreens?\b", UX),
            _p(r"\bbuttons?\b", UX),
            _p(r"\bclick\w*", UX),
            _p(r"\bdashboards?\b", UX),
            _p(r"\bmenus?\b|\bsidebars?\b", UX),
        ),
    ),
    Rule(
        "B-MODEL",
        f"Token, context window or model limitation language outside {IA}",
        (Category.PERSON, Category.ENVIRONMENT, Category.MUSIC),
        (
            _p(r"\btokens?\b", MODEL),
            _p(r"\bcontext (?:windows?|length|limits?|budget)\b", MODEL),
            _p(r"\bLLMs?\b", MODEL, 0),
            _p(r"\blanguage models?\b", MODEL),
            _p(r"\bhallucinat\w*", MODEL),
            _p(r"\bprompts?\b", MODEL),
            _p(r"\bthe model\b|\bmodel(?:'s)? (?:limits?|limitations?|behaviou?r)\b", MODEL),
        ),
    ),
    Rule(
        "B-LOGIC",
        f"Prioritisation, scoring or decision rules inside {ENV}",
        (Category.ENVIRONMENT,),
        (
            _p(r"\bprioriti[sz]\w*|\bpriorit(?:y|ies)\b", PRINCIPLES),
            _p(r"\brank(?:s|ed|ing)?\b", PRINCIPLES),
            _p(r"\bscor(?:e|es|ed|ing)\b", PRINCIPLES),
            _p(r"\bthresholds?\b", PRINCIPLES),
            _p(r"\bweight(?:s|ed|ing)\b", PRINCIPLES),
            _p(r"\bcandidates?\b", PRINCIPLES),
            _p(r"\bqualif(?:y|ies|ied|ication)\b", PRINCIPLES),
            _p(r"\bdecision (?:rules?|logic)\b", DECISIONS),
            _p(r"\brecommend\w*", DECISIONS),
            _p(r"\bshould (?:not )?(?:be )?(?:recover|reclaim|prioriti|rank|chose|choose)\w*", DECISIONS),
        ),
    ),
)


@dataclass(frozen=True)
class Advisory:
    rule: str
    file: str  # the file's name in intake
    file_id: str
    line: int  # 1-based
    match: str
    home: str
    excerpt: str

    def as_data(self) -> dict[str, object]:
        return {
            "rule": self.rule,
            "file": self.file,
            "file_id": self.file_id,
            "line": self.line,
            "match": self.match,
            "suggested_home": self.home,
            "excerpt": self.excerpt,
        }


def _excerpt(line: str, limit: int = 120) -> str:
    text = " ".join(line.split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def clean(line: str) -> str:
    """The line with allowlisted phrases blanked out. Feedback routing reads text the same way (D-36)."""
    for phrase in ALLOWLIST:
        line = phrase.sub(" ", line)
    return line


def lint_file(file: IntakeFile) -> list[Advisory]:
    found: list[Advisory] = []
    rules = [rule for rule in RULES if file.category in rule.checks]
    if not rules:
        return found
    for number, line in enumerate(file.content.split("\n"), start=1):
        text = clean(line)
        for rule in rules:
            for pattern in rule.patterns:
                match = pattern.regex.search(text)
                if match:
                    found.append(Advisory(rule.id, file.name, file.id, number, match.group(0), pattern.home, _excerpt(line)))
                    break
    return found


def lint(files: list[IntakeFile]) -> list[Advisory]:
    """Advisories for every core file, in Ensemble order, then by line and rule order."""
    order = {category: index for index, category in enumerate(Category)}
    advisories = [a for f in sorted(files, key=lambda f: order[f.category]) for a in lint_file(f)]
    return advisories
