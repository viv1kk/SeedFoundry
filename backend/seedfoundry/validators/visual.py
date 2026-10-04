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

Styles the descriptor applies beyond the design system (iteration 1's scoped defects.css, read by
styles.py) are checked too: a card moved off the grid or its gutter, an element wider than its
card, clipped table text (T-19), a font family that is not a font token (T-19), and text colours
against the panel surface (T-20).

It runs in the build (T-17 to T-20), and findings.py groups its problems into
findings (V-1 to V-8) by test and check. Every message starts with the panel's title, and a
format problem shows the panel's own figure in both formats.
"""

from __future__ import annotations

import re
from typing import Any

from seedfoundry.data.model import CLASS_ROLES
from seedfoundry.validators import styles, tokens
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
GEOMETRY = {"margin", "margin-left", "margin-right", "margin-top", "margin-bottom", "top", "left", "right", "bottom", "transform", "translate"}
CLIPPING = {"overflow": {"hidden", "clip"}, "overflow-x": {"hidden", "clip"}, "text-overflow": {"clip", "ellipsis"}}
# Plain words for a measure, and for the renderer's elements a stylesheet rule can target.
MEASURE_WORDS = {"seats": "seat counts", "recoverable_year": "recoverable cost", "unit_cost": "unit cost", "share": "shares", "days_idle": "days idle"}
TARGET_WORDS = {
    "h3": "the title",
    "[data-test='chart-canvas']": "the chart",
    "[data-test='table-scroll']": "the table",
    "[data-test='table-caption']": "the caption",
    "td.is-empty": "the Withheld cells",
    "th:nth-last-child(-n + 2)": "the last two column headers",
    "td:nth-last-child(-n + 2)": "the last two columns",
}
_WIDER = re.compile(r"calc\(\s*100%\s*\+|^(?!100(\.0+)?%)(1\d\d|[2-9]\d\d)(\.\d+)?%$|vw$")  # wider than 100%


def _colours(panel: dict[str, Any]) -> list[tuple[str, str, str | None]]:
    """(where, token, category) for every colour a panel names. A category is the class or
    series the colour stands for, so consistency and fault checks can read it."""
    found: list[tuple[str, str, str | None]] = []
    if "rule_role" in panel:
        found.append(("rule", panel["rule_role"], None))
    for series in panel.get("series", []):
        found.append((f"series {series['id']}", series["role"], series["id"]))
    for n, slice_role in enumerate(panel.get("slice_roles", []), 1):
        found.append((f"slice {n}", slice_role, None))
    for cls, override in panel.get("class_colours", {}).items():
        found.append((f"class {cls}", override["colour"], cls))
    if "withheld" in panel:
        found.append(("withheld label", panel["withheld"]["role"], None))
    if "caption_role" in panel:
        found.append(("caption", panel["caption_role"], None))
    note = panel.get("note")
    if isinstance(note, dict) and "role" in note:
        found.append(("note", note["role"], None))
    return found


def formatted(value: Any, fmt: str | None) -> str | None:
    """A figure in a named format, as frontend/src/dashboard/format.ts writes it; None when the
    format is not a number format."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    if fmt in ("count", "number"):
        return f"{value:,.0f}"
    if fmt == "plain":
        return str(round(value))
    if fmt == "compact":
        size = abs(value)
        return str(round(value)) if size < 1000 else f"{value / 1000:.1f}k" if size < 1_000_000 else f"{value / 1_000_000:.1f}M"
    if fmt == "usd":
        return f"${value:,.0f}"
    if fmt == "usd_compact":
        size = abs(value)
        if size < 1000:
            return f"${value:,.0f}"
        thousands = round(value / 1000)
        return f"${thousands}k" if abs(thousands) < 1000 else f"${value / 1_000_000:.1f}M"
    return None


def _example(payload: dict[str, Any] | None, panel: dict[str, Any], context: str, column: dict[str, Any] | None) -> Any:
    """The panel's own figure for a format problem: a KPI's value, or a table column's total."""
    if payload is None:
        return None
    data = payload["panels"].get(panel["id"], {})
    if context == "kpi":
        return data.get("value")
    if context == "table" and column is not None:
        total = data.get("total")
        return total.get(column["id"]) if isinstance(total, dict) else None
    return None


def _with_example(fmt: str | None, value: Any) -> str:
    shown = formatted(value, fmt)
    return f"{shown} ({fmt})" if shown is not None else str(fmt)


def _text_tokens(panel: dict[str, Any]) -> list[str]:
    return [token for where, token, _ in _colours(panel) if where in ("withheld label", "caption", "note")]


def check(descriptor: dict[str, Any], payload: dict[str, Any] | None = None) -> list[Problem]:
    """Every visual problem in the descriptor; none for the polished variant."""
    problems: list[Problem] = []
    titles = {p["id"]: p["title"] for p in descriptor["panels"]}

    def add(test: str, rule: str, panel: str, expected: Any, shown: Any, message: str, unit: str = "") -> None:
        problems.append(Problem(test, rule, panel, expected, shown, f"{titles.get(panel, 'Dashboard')}: {message}", unit))

    measures = descriptor["measures"]
    class_roles = {c["id"]: c["role"] for c in descriptor["classes"]}
    panels = descriptor["panels"]

    for panel in panels:
        pid = panel["id"]
        mark = panel["mark"]

        # T-17: chart fitness.
        if mark == "pie" and payload is not None:
            # One slice per value; a withheld (None) value has no slice.
            slices = sum(1 for v in payload["panels"][pid].get("values", []) if v is not None)
            if slices > MAX_PIE_SLICES:
                add("T-17", "pie-slices", pid, f"at most {MAX_PIE_SLICES} slices", f"{slices} slices", f"a pie of {slices} slices, where a pie holds at most {MAX_PIE_SLICES}")
        category = panel.get("category", {}).get("field")
        if category in CATEGORY_FIELDS and mark != "bar":
            add("T-17", "categorical-bar", pid, "bars", f"a {mark}", f"a comparison between {category}s drawn as a {mark}, not as bars")

        # T-18: formats and labels.
        contexts: list[tuple[str, str | None, str | None, str, dict[str, Any] | None]] = []
        if mark == "kpi":
            contexts.append(("kpi", panel.get("measure"), panel.get("format"), "the figure", None))
        if "value" in panel:
            contexts.append(("chart", panel["value"].get("measure"), panel["value"].get("format"), "the values", None))
        if mark == "treemap":
            contexts.append(("chart", panel.get("measure"), panel.get("format"), "the cells", None))
            legend = panel.get("legend", {})
            contexts.append(("legend", legend.get("measure"), legend.get("format"), "the legend", None))
        for column in panel.get("columns", []):
            if column.get("measure"):
                contexts.append(("table", column["measure"], column.get("format"), f"the {column['label']} column", column))
        for context, measure, fmt, what, column in contexts:
            expected = measures.get(measure, {}).get(context)
            value = _example(payload, panel, context, column)
            if expected is None:
                add("T-18", "format", pid, f"a declared format for {measure} in {context}", fmt, f"{what} has no declared format")
            elif fmt != expected:
                shown, wanted = _with_example(fmt, value), _with_example(expected, value)
                words = MEASURE_WORDS.get(measure or "", measure)
                add("T-18", "format", pid, wanted, shown, f"{what} reads {shown}, where {words} read {wanted} on every other panel")
            if measure in ("recoverable_year", "unit_cost") and fmt not in MONEY_FORMATS:
                add("T-18", "currency", pid, "US dollars with the $ sign", _with_example(fmt, value), f"{what} shows money without the $ sign")
        if mark in ("bar", "line"):
            for axis_of in ("category", "value"):
                axis = panel.get(axis_of, {}).get("axis") or {}
                if not axis.get("name"):
                    add("T-18", "axis-label", pid, "an axis name", "no name", f"the {axis_of} axis has no name")
            value_of = panel.get("value", {})
            if value_of.get("measure") and not (value_of.get("axis") or {}).get("unit"):
                add("T-18", "axis-unit", pid, "a unit", "no unit", "the value axis has no unit")

        # T-19: palette, class colours, red for faults.
        labels = {**{s["id"]: s.get("label", s["id"]) for s in panel.get("series", [])}, **{c["id"]: c["label"] for c in descriptor["classes"]}}
        for where, token, cat in _colours(panel):
            named = labels.get(cat, where) if cat else where
            allowed = TEXT_ROLES if where in ("withheld label", "caption", "note") else CHART_ROLES
            if token not in allowed or not tokens.is_token(token if where in ("withheld label", "caption", "note") else f"chart-{token}"):
                add("T-19", "palette", pid, "a design token", token, f"{named} drawn in {token}, which is not a palette token")
                continue
            if cat in class_roles and token != class_roles[cat]:
                add("T-19", "class-colour", pid, class_roles[cat], token, f"{named} drawn in {token}, where every other panel draws it in {class_roles[cat]}")
            if token == "negative" and cat not in FAULT_CATEGORIES:
                add("T-19", "red-for-faults", pid, "a role that is not red", token, f"{named} drawn in red ({token}), which is kept for faults")
        if panel.get("font"):
            for role, family in panel["font"].items():
                if family != descriptor["fonts"].get(role):
                    add("T-19", "font", pid, descriptor["fonts"].get(role), family, f"the {role} in {family}, not {descriptor['fonts'].get(role)}")

    # T-19: classes keep Seed v0.1's roles, and red goes to the fault class only.
    for cls in descriptor["classes"]:
        if cls["role"] != CLASS_ROLES.get(cls["id"]):
            add("T-19", "class-colour", "classes", CLASS_ROLES.get(cls["id"]), cls["role"], f"{cls['label']} drawn in {cls['role']}, not {CLASS_ROLES.get(cls['id'])}")
        if cls["role"] == "negative" and cls["id"] not in FAULT_CATEGORIES:
            add("T-19", "red-for-faults", "classes", "a role that is not red", cls["role"], f"{cls['label']} drawn in red, which is kept for faults")
    for role, family in descriptor["fonts"].items():
        if family not in FAMILIES:
            add("T-19", "font", "fonts", "sans or mono", family, f"the {role} font is {family}, not a font token")

    # T-19: layout on the twelve-column grid.
    columns = descriptor["grid"]["columns"]
    for band in descriptor["bands"]:
        members = [p for p in panels if p["band"] == band["id"]]
        row: list[dict[str, Any]] = []
        used = 0
        for panel in members:
            span = panel.get("span")
            if not isinstance(span, int) or not 1 <= span <= columns:
                add("T-19", "grid", panel["id"], f"a span of 1 to {columns}", span, f"a span of {span} is off the {columns}-column grid")
                continue
            if used + span > columns:
                add("T-19", "grid", panel["id"], f"a row of {columns} columns", used + span, f"its row spans {used + span} of {columns} columns")
                used, row = 0, []
            row.append(panel)
            used += span
            if used == columns:
                heights = {p.get("height") for p in row}
                if len(heights) > 1:
                    add("T-19", "grid", row[0]["id"], "one height per row", sorted(h or 0 for h in heights), "cards on its row differ in height")
                used, row = 0, []
        if used:
            add("T-19", "grid", members[-1]["id"], f"rows of {columns} columns", used, f"the {band['id']} band leaves a row part-filled")
    charts = [p for p in panels if p["band"] == "charts"]
    if charts and charts[0].get("span") != columns:
        add("T-19", "grid", charts[0]["id"], columns, charts[0].get("span"), "the first chart does not span the full width")
    if not isinstance(descriptor["grid"].get("gutter"), str):
        add("T-19", "grid", "grid", "one gutter token", descriptor["grid"].get("gutter"), "the grid has no single gutter")

    _check_styles(descriptor, add)

    # T-20: contrast on the panel surface, both themes.
    surface = descriptor["surface"]
    for theme in THEMES:
        background = tokens.colour(theme, surface)
        for panel in panels:
            for token in _text_tokens(panel):
                if token in TEXT_ROLES:
                    ratio = tokens.contrast(tokens.colour(theme, token), background)
                    if ratio < TEXT_CONTRAST:
                        add("T-20", "contrast", panel["id"], TEXT_CONTRAST, round(ratio, 2), f"{token} text at {ratio:.2f}:1 on the card in the {theme} theme (needs {TEXT_CONTRAST}:1)", ":1")
            for where, token, _ in _colours(panel):
                if token in CHART_ROLES and token != "muted" and where not in ("withheld label", "caption", "note"):
                    ratio = tokens.contrast(tokens.colour(theme, f"chart-{token}"), background)
                    if ratio < MARK_CONTRAST:
                        add("T-20", "contrast", panel["id"], MARK_CONTRAST, round(ratio, 2), f"chart-{token} at {ratio:.2f}:1 on the card in the {theme} theme (needs {MARK_CONTRAST}:1)", ":1")
    return problems


def _colour_value(theme: str, value: str) -> str | None:
    """A CSS colour as #rrggbb in a theme: a token through var(), or a raw hex. None otherwise."""
    reference = re.fullmatch(r"var\((--[\w-]+)\)", value)
    if reference:
        return tokens.colour(theme, reference.group(1))
    return value.lower() if re.fullmatch(r"#[0-9a-fA-F]{6}", value) else None


def _check_styles(descriptor: dict[str, Any], add: Any) -> None:
    """T-19 and T-20 over the rules the descriptor's stylesheet applies (styles.py); none for the
    polished descriptor. One problem per rule and check (per theme for contrast)."""
    marks = {p["id"]: p["mark"] for p in descriptor["panels"]}
    surface = descriptor["surface"]
    for rule in styles.applied(descriptor):
        where = rule.panel or "dashboard"
        part = TARGET_WORDS.get(rule.target, f"the element {rule.target}") if rule.target else "the card"
        moved = [f"{p}: {v}" for p, v in rule.declarations if not rule.target and p in GEOMETRY]
        if moved:
            shown = "; ".join(moved)
            add("T-19", "grid", where, "on the grid, with the band's one gutter", shown, f"the card is moved off the grid ({shown})")
        wide = [f"{p}: {v}" for p, v in rule.declarations if p in ("width", "min-width") and _WIDER.search(v)]
        if wide:
            shown = "; ".join(wide)
            add("T-19", "overflow", where, "at most the width of its card", shown, f"{part} is wider than its card ({shown})")
        clipped = [f"{p}: {v}" for p, v in rule.declarations if v in CLIPPING.get(p, ())]
        if clipped and marks.get(where) == "table":
            shown = "; ".join(clipped)
            add("T-19", "truncation", where, "every column readable", shown, f"{part} {'are' if part.endswith('s') else 'is'} clipped ({shown})")
        family = rule.value("font-family")
        if family and not family.startswith("var(--font-"):
            add("T-19", "font", where, "a font token (Inter or JetBrains Mono)", family, f"{part} is set in {family}, not a font token")
        colour = rule.value("color")
        if colour:
            for theme in THEMES:
                shown_colour = _colour_value(theme, colour)
                if shown_colour is None:
                    add("T-19", "palette", where, "a design token", colour, f"{part} is coloured {colour}, which is not a token")
                    break
                ratio = tokens.contrast(shown_colour, tokens.colour(theme, surface))
                if ratio < TEXT_CONTRAST:
                    add("T-20", "contrast", where, TEXT_CONTRAST, round(ratio, 2), f"{part} ({colour}) at {ratio:.2f}:1 on the card in the {theme} theme (needs {TEXT_CONTRAST}:1)", ":1")
