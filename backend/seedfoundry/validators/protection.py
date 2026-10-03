"""Protection probes (T-13, FR-T-5, seed-reuse-notes.md §2.6, D-62).

Rules are derived from the intake's Protection layer (environment.md, the `##` section whose title
names Protection), line by line, by fixed patterns: a line that says the Seed is read only, that it
never removes or changes a seat, that cost is shown only where a unit price exists, that names stay
at the seat level, or that the data stays inside the sandbox gives the rules below, each citing its
file, section and line. Nothing is printed: change the Protection layer and the rules, and so the
probe results, change with it.

Each probe is a request, as in Seed v0.1's policy evaluation: an action, a resource and facts,
never a rule. Every covering rule whose facts hold matches; the strictest effect wins (DENY over
ESCALATE over ALLOW) and the most specific rule of that effect is cited. A request missing a fact
some covering rule depends on is denied under the default rule, and so is a request no rule
allows. The rule ids are SeedFoundry's (P-1, P-2, ...), never Seed v0.1's (requirements §9).

T-13 passes when every probe gets its expected effect from a rule of the Protection layer (one
probe expects the default rule: a missing fact). It warns when a probe is decided by the default
rule where a stated rule was expected (the layer does not cover it), or an allowed request is
denied. It fails when a request the layer should stop is allowed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from seedfoundry.intake import assay
from seedfoundry.state import Category, IntakeFile

ALLOW, ESCALATE, DENY = "ALLOW", "ESCALATE", "DENY"
STRICTNESS = {ALLOW: 0, ESCALATE: 1, DENY: 2}
DEFAULT = "default"
WRITES = ("remove", "reassign", "change", "delete", "write")
ANY = "*"


@dataclass(frozen=True)
class Rule:
    id: str
    effect: str
    actions: tuple[str, ...]
    resource: str
    when: tuple[tuple[str, str], ...]
    file: str
    section: str
    line: int
    text: str

    def covers(self, action: str, resource: str) -> bool:
        return action in self.actions and self.resource in (resource, ANY)

    def as_data(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "effect": self.effect,
            "actions": list(self.actions),
            "resource": self.resource,
            "when": dict(self.when),
            "file": self.file,
            "section": self.section,
            "line": self.line,
            "text": self.text,
        }


@dataclass(frozen=True)
class Probe:
    id: str
    request: str  # what the probe asks, in words
    action: str
    resource: str
    facts: tuple[tuple[str, str], ...]
    expected: str  # the effect a sound Protection layer gives
    by_rule: bool = True  # decided by a stated rule; False when the default rule is the right answer


@dataclass
class Decision:
    probe: Probe
    effect: str
    rule: Rule | None
    reason: str
    outcome: str = field(default="")  # as-expected, default-only, over-restrictive, let-through

    @property
    def basis(self) -> str:
        if self.rule is None:
            return f"the default rule ({self.reason})"
        return f"{self.rule.id} ({self.rule.file}, {self.rule.section}, line {self.rule.line})"

    def as_data(self) -> dict[str, Any]:
        return {
            "probe": self.probe.id,
            "request": self.probe.request,
            "expected": self.probe.expected,
            "effect": self.effect,
            "rule": self.rule.id if self.rule else DEFAULT,
            "basis": self.basis,
            "outcome": self.outcome,
        }


# The probe set: requests a License Optimization Seed's protection must stop, three it must allow,
# and one missing a fact the cost rules depend on.
PROBES: tuple[Probe, ...] = (
    Probe("PB-1", "remove an Unused seat from the License Management System", "remove", "seat", (), DENY),
    Probe("PB-2", "reassign a Leaver's seat to another person", "reassign", "seat", (), DENY),
    Probe("PB-3", "show recoverable cost for an unpriced product as $0", "show_cost", "product", (("priced", "no"),), DENY),
    Probe("PB-4", "show recoverable cost for a priced product", "show_cost", "product", (("priced", "yes"),), ALLOW),
    Probe("PB-5", "show recoverable cost without knowing whether the product is priced", "show_cost", "product", (), DENY, by_rule=False),
    Probe("PB-6", "list assignee names in a vendor summary", "show_names", "names", (("level", "summary"),), DENY),
    Probe("PB-7", "list assignee names in the Seats table", "show_names", "names", (("level", "seat"),), ALLOW),
    Probe("PB-8", "export assignee names", "export", "names", (), DENY),
    Probe("PB-9", "send the seat dataset outside the sandbox", "send", "dataset", (("destination", "outside"),), DENY),
    Probe("PB-10", "read the seat records", "read", "seat", (), ALLOW),
)

# Line patterns and the rules each gives: (effect, actions, resource, when).
Template = tuple[str, tuple[str, ...], str, tuple[tuple[str, str], ...]]
_VERBS = {"remov": "remove", "reassign": "reassign", "chang": "change", "delet": "delete", "modif": "change", "writ": "write"}
_READ_ONLY = re.compile(r"\bread[- ]only\b", re.I)
_NEVER_WRITES = re.compile(r"\bnever\b[^.]*\b(remov|reassign|chang|delet|modif|writ)", re.I)
_COST = re.compile(r"\b(cost|price)\b[^.]*\b(unit price|priced)\b|\bunpriced\b[^.]*\bwithheld\b", re.I)
_NAMES = re.compile(r"\bnames?\b[^.]*\bonly at the seat level\b", re.I)
_NAMES_EXPORT = re.compile(r"\bnames?\b[^.]*\bnever in exports?\b", re.I)
_EGRESS = re.compile(r"\b(stays|kept|remains) inside the sandbox\b|\bnothing is sent outside\b|\bno egress\b", re.I)


def _templates(text: str) -> list[Template]:
    found: list[Template] = []
    if _READ_ONLY.search(text):
        found.append((ALLOW, ("read",), ANY, ()))
        found.append((DENY, WRITES, ANY, ()))
    never = _NEVER_WRITES.search(text)
    if never:
        verbs = tuple(dict.fromkeys(v for stem, v in _VERBS.items() if re.search(rf"\b{stem}", text[never.start() :], re.I)))
        found.append((DENY, verbs, "seat" if re.search(r"\bseats?\b", text, re.I) else ANY, ()))
    if _COST.search(text):
        found.append((ALLOW, ("show_cost",), "product", (("priced", "yes"),)))
        found.append((DENY, ("show_cost",), "product", (("priced", "no"),)))
    if _NAMES.search(text):
        found.append((ALLOW, ("show_names",), "names", (("level", "seat"),)))
        found.append((DENY, ("show_names",), "names", (("level", "summary"),)))
    if _NAMES_EXPORT.search(text):
        found.append((DENY, ("export",), "names", ()))
    if _EGRESS.search(text):
        found.append((DENY, ("send",), "dataset", (("destination", "outside"),)))
    return found


def protection_lines(environment: IntakeFile | None) -> tuple[str, list[tuple[int, str]]]:
    """The Protection layer's title and its numbered lines, sub-sections included; ("", []) without one."""
    if environment is None:
        return "", []
    parts = assay.sections(environment.content)
    for index, part in enumerate(parts):
        if part.level == 2 and "protection" in assay.key(part.title):
            lines = [(part.line + 1 + i, text) for i, text in enumerate(part.body)]
            for sub in parts[index + 1 :]:
                if sub.level <= 2:
                    break
                lines += [(sub.line + 1 + i, text) for i, text in enumerate(sub.body)]
            return part.title, lines
    return "", []


def rules(files: list[IntakeFile]) -> list[Rule]:
    """Every rule the intake's Protection layer gives, in line order."""
    environment = next((f for f in files if f.category == Category.ENVIRONMENT), None)
    section, lines = protection_lines(environment)
    out: list[Rule] = []
    for number, text in lines:
        sentence = text.strip().lstrip("-*+ ").strip()
        if not sentence or sentence.startswith("#"):
            continue
        for effect, actions, resource, when in _templates(sentence):
            out.append(Rule(f"P-{len(out) + 1}", effect, actions, resource, when, environment.name, section, number, sentence))  # type: ignore[union-attr]
    return out


def evaluate(ruleset: list[Rule], probe: Probe) -> Decision:
    """Seed v0.1's evaluation (seed-reuse-notes.md §2.6) of one request."""
    facts = dict(probe.facts)
    covering = [r for r in ruleset if r.covers(probe.action, probe.resource)]
    missing = sorted({key for r in covering for key, _ in r.when if key not in facts})
    if missing:
        return Decision(probe, DENY, None, f"the request does not state {', '.join(missing)}")
    matching = [r for r in covering if all(facts.get(k) == v for k, v in r.when)]
    if not matching:
        return Decision(probe, DENY, None, "no rule allows it")
    strictest = max(STRICTNESS[r.effect] for r in matching)
    of_effect = [r for r in matching if STRICTNESS[r.effect] == strictest]
    # Most specific: the most facts, then a named resource over any; the earliest line breaks a tie.
    chosen = min(of_effect, key=lambda r: (-len(r.when), r.resource == ANY, ruleset.index(r)))
    return Decision(probe, chosen.effect, chosen, "")


def judge(ruleset: list[Rule], probes: tuple[Probe, ...] = PROBES) -> tuple[list[Decision], str]:
    """A decision per probe with its outcome, and T-13's status (pass, warn or fail)."""
    decisions = []
    for probe in probes:
        decision = evaluate(ruleset, probe)
        if probe.expected == DENY and decision.effect != DENY:
            decision.outcome = "let-through"
        elif decision.effect != probe.expected:
            decision.outcome = "over-restrictive"
        elif probe.by_rule and decision.rule is None:
            decision.outcome = "default-only"
        else:
            decision.outcome = "as-expected"
        decisions.append(decision)
    outcomes = {d.outcome for d in decisions}
    status = "fail" if "let-through" in outcomes else "warn" if outcomes - {"as-expected"} else "pass"
    return decisions, status


def run(files: list[IntakeFile], probes: tuple[Probe, ...] = PROBES) -> tuple[list[Rule], list[Decision], str]:
    """The rules the intake gives, a decision per probe, and T-13's status."""
    ruleset = rules(files)
    decisions, status = judge(ruleset, probes)
    return ruleset, decisions, status
