"""Visual QA (T-17 to T-20, FR-T-4, build-simulation.md §6.3), run over the dashboard descriptor
and the resolved token values of tokens.css, in both themes.

- T-17 chart fitness: a pie has at most six slices; a comparison between categories is a bar.
- T-18 formats and labels: one format per measure in each context (chart, KPI, table), money
  always in dollars; every chart axis has a name, and a value axis whose measure has a unit
  states it.
- T-19 palette and layout: every colour is a design token (a chart role, or a text token for
  text), never a raw value; a utilisation class has one colour on every panel; red (`negative`)
  only for a fault, which here is the Leaver class (an access finding); each band packs onto the
  twelve-column grid with one gutter, the first chart spans the full width, and charts on one
  row share a height; one font family per role.
- T-20 contrast: every text colour the descriptor names against the panel surface at 4.5:1, and
  every chart role it draws with at 3:1 (except `muted`), in both themes.

Minimal in M7 (the polished descriptor passes); M9 maps problems to findings (V-1 to V-8) and
adds what M8's defects.css applies.
"""

from __future__ import annotations

from typing import Any

from seedfoundry.data.model import CLASS_ROLES
from seedfoundry.validators import tokens
from seedfoundry.validators.problems import Problem

THEMES = ("light", "dark")
CHART_ROLES = {f"series-{n}" for n in range(1, 9)} | {"positive", "warning", "negative", "anomaly", "baseline", "muted"}
TEXT_ROLES = {"text-primary", "text-secondary", "text-muted"}
FAULT_CATEGORIES = {"leaver"}  # red is reserved for faults; a Leaver seat is an access finding
CATEGORY_FIELDS = {"product", "vendor", "department"}
MONEY_FORMATS = {"usd", "usd_compact"}
FAMILIES = {"sans", "mono"}
MAX_PIE_SLICES = 6
TEXT_CONTRAST = 4.5
MARK_CONTRAST = 3.0


def _colours(panel: dict[str, Any]) -> list[tuple[str, str, str | None]]:
    """(where, token, category) for every colour a panel names. A category is the class or
    series the colour stands for, so consistency and fault checks can read it."""
    found: list[tuple[str, str, str | None]] = []
    if "rule_role" in panel:
        found.append(("rule", panel["rule_role"], None))
    for series in panel.get("series", []):
        found.append((f"series {series['id']}", series["role"], series["id"]))
    if "withheld" in panel:
        found.append(("withheld label", panel["withheld"]["role"], None))
    if "caption_role" in panel:
        found.append(("caption", panel["caption_role"], None))
    note = panel.get("note")
    if isinstance(note, dict) and "role" in note:
        found.append(("note", note["role"], None))
    return found


def _text_tokens(panel: dict[str, Any]) -> list[str]:
    return [token for where, token, _ in _colours(panel) if where in ("withheld label", "caption", "note")]


def check(descriptor: dict[str, Any], payload: dict[str, Any] | None = None) -> list[Problem]:
    """Every visual problem in the descriptor; none for the polished variant."""
    problems: list[Problem] = []

    def add(test: str, rule: str, panel: str, expected: Any, shown: Any, message: str) -> None:
        problems.append(Problem(test, rule, panel, expected, shown, message))

    measures = descriptor["measures"]
    class_roles = {c["id"]: c["role"] for c in descriptor["classes"]}
    panels = descriptor["panels"]

    for panel in panels:
        pid = panel["id"]
        mark = panel["mark"]

        # T-17: chart fitness.
        if mark == "pie" and payload is not None:
            slices = len(payload["panels"][pid].get("categories", []))
            if slices > MAX_PIE_SLICES:
                add("T-17", "pie-slices", pid, f"at most {MAX_PIE_SLICES} slices", slices, f"a pie with {slices} slices")
        category = panel.get("category", {}).get("field")
        if category in CATEGORY_FIELDS and mark != "bar":
            add("T-17", "categorical-bar", pid, "bar", mark, f"a comparison between {category}s drawn as {mark}")

        # T-18: formats and labels.
        contexts = []
        if mark == "kpi":
            contexts.append(("kpi", panel.get("measure"), panel.get("format")))
        if "value" in panel:
            contexts.append(("chart", panel["value"].get("measure"), panel["value"].get("format")))
        if mark == "treemap":
            contexts.append(("chart", panel.get("measure"), panel.get("format")))
            legend = panel.get("legend", {})
            contexts.append(("legend", legend.get("measure"), legend.get("format")))
        for column in panel.get("columns", []):
            if column.get("measure"):
                contexts.append(("table", column["measure"], column.get("format")))
        for context, measure, fmt in contexts:
            expected = measures.get(measure, {}).get(context)
            if expected is None:
                add("T-18", "format", pid, f"a declared format for {measure} in {context}", fmt, f"{measure} has no {context} format")
            elif fmt != expected:
                add("T-18", "format", pid, expected, fmt, f"{measure} formatted as {fmt}, not {expected}")
            if measure in ("recoverable_year", "unit_cost") and fmt not in MONEY_FORMATS:
                add("T-18", "currency", pid, "a dollar format", fmt, f"{measure} shown without its currency")
        if mark in ("bar", "line"):
            for axis_of in ("category", "value"):
                axis = panel.get(axis_of, {}).get("axis") or {}
                if not axis.get("name"):
                    add("T-18", "axis-label", pid, "an axis name", None, f"the {axis_of} axis has no name")
            value = panel.get("value", {})
            if value.get("measure") and not (value.get("axis") or {}).get("unit"):
                add("T-18", "axis-unit", pid, "a unit", None, "the value axis has no unit")

        # T-19: palette, class colours, red for faults.
        for where, token, cat in _colours(panel):
            allowed = TEXT_ROLES if where in ("withheld label", "caption", "note") else CHART_ROLES
            if token not in allowed or not tokens.is_token(token if where in ("withheld label", "caption", "note") else f"chart-{token}"):
                add("T-19", "palette", pid, "a design token", token, f"{where} drawn in {token}, which is not a token for it")
                continue
            if cat in class_roles and token != class_roles[cat]:
                add("T-19", "class-colour", pid, class_roles[cat], token, f"{cat} drawn in {token}, not {class_roles[cat]}")
            if token == "negative" and cat not in FAULT_CATEGORIES:
                add("T-19", "red-for-faults", pid, "a non-red role", token, f"{where} is red but is not a fault")
        if panel.get("font"):
            for role, family in panel["font"].items():
                if family != descriptor["fonts"].get(role):
                    add("T-19", "font", pid, descriptor["fonts"].get(role), family, f"{role} in {family}")

    # T-19: classes keep Seed v0.1's roles, and red goes to the fault class only.
    for cls in descriptor["classes"]:
        if cls["role"] != CLASS_ROLES.get(cls["id"]):
            add("T-19", "class-colour", "classes", CLASS_ROLES.get(cls["id"]), cls["role"], f"{cls['label']} drawn in {cls['role']}")
        if cls["role"] == "negative" and cls["id"] not in FAULT_CATEGORIES:
            add("T-19", "red-for-faults", "classes", "a non-red role", cls["role"], f"{cls['label']} is red but is not a fault")
    for role, family in descriptor["fonts"].items():
        if family not in FAMILIES:
            add("T-19", "font", "fonts", "sans or mono", family, f"{role} in {family}")

    # T-19: layout on the twelve-column grid.
    columns = descriptor["grid"]["columns"]
    for band in descriptor["bands"]:
        members = [p for p in panels if p["band"] == band["id"]]
        row: list[dict[str, Any]] = []
        used = 0
        for panel in members:
            span = panel.get("span")
            if not isinstance(span, int) or not 1 <= span <= columns:
                add("T-19", "grid", panel["id"], f"a span of 1 to {columns}", span, "off the grid")
                continue
            if used + span > columns:
                add("T-19", "grid", panel["id"], f"a row of {columns} columns", used + span, "the row overflows the grid")
                used, row = 0, []
            row.append(panel)
            used += span
            if used == columns:
                heights = {p.get("height") for p in row}
                if len(heights) > 1:
                    add("T-19", "grid", row[0]["id"], "one height per row", sorted(h or 0 for h in heights), "cards on one row differ in height")
                used, row = 0, []
        if used:
            add("T-19", "grid", members[-1]["id"], f"rows of {columns} columns", used, f"the {band['id']} band leaves a row part-filled")
    charts = [p for p in panels if p["band"] == "charts"]
    if charts and charts[0].get("span") != columns:
        add("T-19", "grid", charts[0]["id"], columns, charts[0].get("span"), "the first chart does not span the full width")
    if not isinstance(descriptor["grid"].get("gutter"), str):
        add("T-19", "grid", "grid", "one gutter token", descriptor["grid"].get("gutter"), "uneven gutters")

    # T-20: contrast on the panel surface, both themes.
    surface = descriptor["surface"]
    for theme in THEMES:
        background = tokens.colour(theme, surface)
        for panel in panels:
            for token in _text_tokens(panel):
                if token in TEXT_ROLES:
                    ratio = tokens.contrast(tokens.colour(theme, token), background)
                    if ratio < TEXT_CONTRAST:
                        add("T-20", "contrast", panel["id"], f"{TEXT_CONTRAST}:1", round(ratio, 2), f"{token} on {surface} in {theme}")
            for where, token, _ in _colours(panel):
                if token in CHART_ROLES and token != "muted" and where not in ("withheld label", "caption", "note"):
                    ratio = tokens.contrast(tokens.colour(theme, f"chart-{token}"), background)
                    if ratio < MARK_CONTRAST:
                        add("T-20", "contrast", panel["id"], f"{MARK_CONTRAST}:1", round(ratio, 2), f"chart-{token} on {surface} in {theme}")
    return problems
