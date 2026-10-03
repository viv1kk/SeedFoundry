"""The styles a dashboard's descriptor applies beyond the design system: the rules of the scoped
stylesheet it names (frontend/src/styles/defects.css for iteration 1's rough variant, D-13, D-60),
read so visual QA can check what the browser will draw (FR-T-4) and not only the descriptor.

A minimal reader, not a CSS engine: it splits the sheet into rules, drops comments, and keeps each
rule's selectors and declarations. A rule's panel is the `[data-panel=...]` its selector names;
its target is what follows that (empty when the rule styles the card itself). The polished
descriptor names no sheet, so it applies no rule.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

STYLES_DIR = Path(__file__).resolve().parents[3] / "frontend" / "src" / "styles"

_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")
_PANEL = re.compile(r"""\[data-panel=['"]?([\w-]+)['"]?\]""")


@dataclass(frozen=True)
class Rule:
    selector: str
    declarations: tuple[tuple[str, str], ...]

    @property
    def panel(self) -> str | None:
        found = _PANEL.search(self.selector)
        return found.group(1) if found else None

    @property
    def target(self) -> str:
        """What the rule styles inside its panel: "" for the card itself, else the rest of the selector."""
        found = _PANEL.search(self.selector)
        return self.selector[found.end() :].strip() if found else self.selector

    def value(self, prop: str) -> str | None:
        return next((v for p, v in self.declarations if p == prop), None)


def _declarations(body: str) -> tuple[tuple[str, str], ...]:
    out = []
    for part in body.split(";"):
        if ":" not in part:
            continue
        prop, value = part.split(":", 1)
        out.append((prop.strip().lower(), value.replace("!important", "").strip()))
    return tuple(out)


def parse(css: str) -> list[Rule]:
    """One Rule per selector of every rule, in sheet order."""
    rules = []
    for selectors, body in _RULE.findall(_COMMENT.sub("", css)):
        declarations = _declarations(body)
        for selector in selectors.split(","):
            rules.append(Rule(" ".join(selector.split()), declarations))
    return rules


@cache
def _sheet(path: Path) -> tuple[Rule, ...]:
    return tuple(parse(path.read_text(encoding="utf-8")))


def sheet(name: str, directory: Path = STYLES_DIR) -> list[Rule]:
    return list(_sheet(directory / name))


def applied(descriptor: dict[str, Any], directory: Path = STYLES_DIR) -> list[Rule]:
    """The rules the descriptor's stylesheet applies inside its root class; none without one."""
    styles = descriptor.get("styles")
    if not styles:
        return []
    root = f".{styles['root_class']}"
    return [rule for rule in sheet(styles["sheet"], directory) if rule.selector.split(" ", 1)[0] == root]
