"""Iteration 1's defect overlay (D-13, FR-D-2, FR-D-4, seed-reuse-notes.md §5.8, D-60).

The rough dashboard is the polished one plus this overlay. Nothing here stores a figure: each
patch is a rule over the descriptor or over the payload the query engine built from the seat
rows, so it applies at whatever drill level the payload is for (R-9). The overlay is a named list
of patches, one per catalogue defect, in three layers:

- `descriptor`: a change to the polished descriptor (a mark, a colour role, a format, an axis,
  a declared latency);
- `payload`: a rule that rewrites figures the query engine computed, derived from the true
  figures or the rows by a fixed rule (N-1 to N-5);
- `styles`: rules in frontend/src/styles/defects.css, every one under ROOT_CLASS, which only the
  rough dashboard's root element carries (R-1). The descriptor names the class and the sheet.

The validators never read this list (D-14): they recompute from the rows, the descriptor and the
resolved styles. Each patch also says what happens to it at a deep drill level, where some fall
away because the filter leaves nothing for them to distort.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from seedfoundry.data.model import CLASSES, Seat

ROOT_CLASS = "defects-overlay"
STYLESHEET = "defects.css"  # frontend/src/styles/
N1_FACTOR = Decimal("1.2")
N2_FACTOR = Decimal("1.12")
LATENCY_MS = 4500
# V-3: the one raw colour on the dashboard. ECharts' own first default colour, which is what a
# chart shows when nobody bound the class to its role; it is in neither theme's palette.
OFF_PALETTE = "#5470c6"
PIE_ROLES = [f"series-{n}" for n in range(1, 9)]


@dataclass(frozen=True)
class Context:
    """What a payload rule may read: the seat rows in the filter and their true measures."""

    seats: list[Seat]
    totals: dict[str, int]


@dataclass(frozen=True)
class Patch:
    defect: str
    panels: tuple[str, ...]
    layer: str  # descriptor, payload or styles
    shows: str  # what the viewer sees
    rule: str  # how it is derived from the data or the polished descriptor
    deep: str  # what it does at a deep drill level
    descriptor: Callable[[dict[str, Any]], None] | None = None
    payload: Callable[[dict[str, Any], Context], None] | None = None

    def as_data(self) -> dict[str, Any]:
        return {
            "defect": self.defect,
            "panels": list(self.panels),
            "layer": self.layer,
            "shows": self.shows,
            "rule": self.rule,
            "deep": self.deep,
        }


def _panel(desc: dict[str, Any], panel_id: str) -> dict[str, Any]:
    return next(p for p in desc["panels"] if p["id"] == panel_id)


def _scale(value: int | float, factor: Decimal, places: str = "1") -> Any:
    """value x factor, rounded half up to `places` (integers stay integers)."""
    scaled = (Decimal(str(value)) * factor).quantize(Decimal(places), rounding=ROUND_HALF_UP)
    return int(scaled) if places == "1" else float(scaled)


# Payload rules (N-1 to N-5)


def _n1(panels: dict[str, Any], ctx: Context) -> None:
    bars = panels["entitlement"]
    bars["series"]["entitled"] = [_scale(v, N1_FACTOR) for v in bars["series"]["entitled"]]
    shown = dict(zip((c["id"] for c in bars["categories"]), bars["series"]["entitled"], strict=True))
    for target in bars["targets"]:  # the keyboard read-out says what the bar shows
        target["value"] = shown[target["step"][-1]]


def _n2(panels: dict[str, Any], ctx: Context) -> None:
    for item in panels["seats-treemap"]["legend"]:
        item["share"] = _scale(item["share"], N2_FACTOR, "0.1")


def _n3(panels: dict[str, Any], ctx: Context) -> None:
    panels["k-recoverable"]["value"] = sum(
        12 * s.unit_cost for s in ctx.seats if s.utilisation_class in ("unused", "underused") and s.unit_cost is not None
    )


def _n4(panels: dict[str, Any], ctx: Context) -> None:
    panels["seats"]["footer"]["total"] = ctx.totals["assigned"]


def largest_row(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The candidate row with the most entitled seats; the first in table order breaks a tie."""
    return max(rows, key=lambda r: r["entitled"], default=None)


def _n5(panels: dict[str, Any], ctx: Context) -> None:
    table = panels["candidates"]
    row = largest_row(table["rows"])
    if row is None:
        return
    for key in ("entitled", *CLASSES, "recoverable_seats"):
        table["total"][key] += row[key]
    table["total"]["recoverable_year"] += row["recoverable_year"] or 0


# Descriptor patches (V-1 to V-5, L-1)


def _v1(desc: dict[str, Any]) -> None:
    _panel(desc, "recoverable").update(mark="pie", slice_roles=list(PIE_ROLES))


def _v2(desc: dict[str, Any]) -> None:
    next(s for s in _panel(desc, "trend")["series"] if s["id"] == "in_use")["role"] = "negative"


def _v3(desc: dict[str, Any]) -> None:
    _panel(desc, "seats-treemap")["class_colours"] = {"unused": {"colour": OFF_PALETTE}}
    next(s for s in _panel(desc, "entitlement")["series"] if s["id"] == "active")["role"] = "series-3"


def _v4(desc: dict[str, Any]) -> None:
    _panel(desc, "k-entitled")["format"] = "plain"
    _panel(desc, "k-active")["format"] = "compact"
    next(c for c in _panel(desc, "candidates")["columns"] if c["id"] == "recoverable_year")["format"] = "number"


def _v5(desc: dict[str, Any]) -> None:
    for panel_id in ("entitlement", "trend"):
        panel = _panel(desc, panel_id)
        panel["category"]["axis"] = {"name": "", "unit": None}
        panel["value"]["axis"] = {"name": "", "unit": None}


def _l1(desc: dict[str, Any]) -> None:
    _panel(desc, "seats-treemap")["latency_ms"] = LATENCY_MS


OVERLAY: tuple[Patch, ...] = (
    Patch(
        "N-1",
        ("entitlement",),
        "payload",
        "Entitled bars at 1.2 times their true size, so they sum to more than the Entitled KPI",
        "each product's Entitled bar is its true seat count x 1.2, rounded half up",
        "holds at every level; with one product (a product or class drill) the one bar is still 1.2 x the KPI",
        payload=_n1,
    ),
    Patch(
        "N-2",
        ("seats-treemap",),
        "payload",
        "Treemap legend shares at 1.12 times their true value, summing to about 112%",
        "each class's share of entitled seats x 1.12, rounded half up to one decimal",
        "holds at every level; at a class drill the one class reads 112.0%",
        payload=_n2,
    ),
    Patch(
        "N-3",
        ("k-recoverable", "recoverable"),
        "payload",
        "Recoverable a year computed over Unused and Underused seats, so it differs from the cost by product",
        "sum of unit cost x 12 over priced Unused and Underused seats, instead of Unused, Leaver and Unassigned",
        "falls away where both sums are equal: a drill to an unpriced product, or to the Active or Unused class",
        payload=_n3,
    ),
    Patch(
        "N-4",
        ("seats",),
        "payload",
        "Seats footer Total shows the assigned count, not the sum of the class counts",
        "footer total = seats with an assignee (every class but Unassigned)",
        "falls away at a class drill other than Unassigned, where every seat is assigned",
        payload=_n4,
    ),
    Patch(
        "N-5",
        ("candidates",),
        "payload",
        "Optimisation candidates total row counts the largest product's row twice",
        "total row = sum of the rows + the row with the most entitled seats (first in table order on a tie)",
        "holds at every level; with one product the total row reads twice that row",
        payload=_n5,
    ),
    Patch(
        "V-1",
        ("recoverable",),
        "descriptor",
        "Recoverable cost by product drawn as a pie, one slice per priced product",
        "mark bar becomes pie over the same data; slices cycle series-1 to series-8",
        "the pie stays at every level; more than six slices only where more than six priced products are in the filter (All products)",
        descriptor=_v1,
    ),
    Patch(
        "V-2",
        ("trend",),
        "descriptor",
        "The In use line drawn in red, a normal series in the fault colour",
        "series in_use bound to the negative role instead of positive",
        "holds at every level",
        descriptor=_v2,
    ),
    Patch(
        "V-3",
        ("seats-treemap", "entitlement"),
        "descriptor",
        "Unused in an off-palette blue in the treemap; Active in teal on the bar chart while green on the treemap",
        f"treemap class colour for unused set to {OFF_PALETTE}; entitlement series active bound to series-3",
        "holds wherever the treemap has an Unused cell (not at a class drill to another class); the bar's Active teal holds at every level",
        descriptor=_v3,
    ),
    Patch(
        "V-4",
        ("k-entitled", "k-assigned", "k-active", "candidates"),
        "descriptor",
        "KPIs in three number formats (for example 13050, 12,401 and 8.3k); candidates' recoverable figures without the dollar sign",
        "k-entitled format plain, k-active compact (k-assigned keeps count); candidates recoverable_year format number",
        "holds at every level",
        descriptor=_v4,
    ),
    Patch(
        "V-5",
        ("entitlement", "trend"),
        "descriptor",
        "No axis names or units on the per-product bars and the monthly trend",
        "category and value axis names emptied and units removed on both charts",
        "holds at every level",
        descriptor=_v5,
    ),
    Patch(
        "V-6",
        ("k-assigned", "k-active", "k-idle", "seats-treemap", "seats"),
        "styles",
        "Uneven KPI gutters, one KPI card off the grid, the treemap wider than its card, the last two Seats columns clipped",
        "defects.css: margins on two KPI cards, an offset on Unused or underused, the treemap canvas 100% + 40px, the last two Seats columns 34px wide with overflow hidden",
        "holds at every level",
    ),
    Patch(
        "V-7",
        ("trend",),
        "styles",
        "The monthly trend's title in a system serif",
        "defects.css: the trend title's font-family is Georgia, Times New Roman, serif",
        "holds at every level",
    ),
    Patch(
        "V-8",
        ("candidates",),
        "styles",
        "Optimisation candidates caption and Withheld notes in a light grey below 4.5:1",
        "defects.css: caption and empty-cell text coloured with --border-default, a border token, on the card surface",
        "holds wherever a Withheld cell is shown; the caption holds at every level",
    ),
    Patch(
        "L-1",
        ("seats-treemap",),
        "descriptor",
        "Seats by vendor and product waits 4.5 s behind a spinner while the rest of the page is ready",
        f"latency_ms {LATENCY_MS} declared on the treemap, against the 1.0 s budget; the browser waits that long before drawing it",
        "holds at every level: the treemap waits again on each drill and on reload, not on paging or sorting the Seats table",
        descriptor=_l1,
    ),
)


def apply_descriptor(polished: dict[str, Any]) -> dict[str, Any]:
    """The rough descriptor: the polished one (a copy) with every descriptor patch applied, the
    variant set and the scoped stylesheet named."""
    desc = {**copy.deepcopy(polished), "variant": "rough", "styles": {"root_class": ROOT_CLASS, "sheet": STYLESHEET}}
    for patch in OVERLAY:
        if patch.descriptor:
            patch.descriptor(desc)
    return desc


def apply_payload(panels: dict[str, Any], seats: list[Seat], totals: dict[str, int]) -> None:
    """Rewrite, in place, the figures the payload rules distort. `panels` was built from `seats`."""
    ctx = Context(seats, totals)
    for patch in OVERLAY:
        if patch.payload:
            patch.payload(panels, ctx)


def as_data() -> dict[str, Any]:
    return {
        "applies_to_iteration": 1,
        "root_class": ROOT_CLASS,
        "stylesheet": f"frontend/src/styles/{STYLESHEET}",
        "patches": [p.as_data() for p in OVERLAY],
    }
