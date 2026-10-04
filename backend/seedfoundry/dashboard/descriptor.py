"""The License Optimization dashboard descriptor (FR-D-4, seed-reuse-notes.md §2.5 and §5).

One generic renderer draws the dashboard from this. A panel names its mark, its data binding,
its layout (band, span on the twelve-column grid, height) and its colours as chart roles, never
hex (D-5, D-37). Number formats are named per measure. The descriptor holds no data: the payload
is built from the seat rows (payload.py), so the defect overlay (overlay.py) can patch this
descriptor and the validators can recompute every figure from the rows.

This is the polished variant, iteration 2's. Iteration 1's is this plus the defect overlay
(overlay.py, D-13, D-60).
"""

from __future__ import annotations

import copy
from typing import Any

from seedfoundry.dashboard import overlay
from seedfoundry.data.model import CLASS_LABELS, CLASS_ROLES, CLASSES, RECOVERABLE

DASHBOARD_ID = "license-optimization"
GRID_COLUMNS = 12

# Font roles: one family per role (seed-reuse-notes.md §1.4).
FONTS = {"title": "sans", "label": "sans", "figure": "mono", "id": "mono"}

# One format per measure, on every panel where the measure appears (environment.md, Styling):
# counts with thousands separators; money in US dollars, compact on charts and KPIs and whole
# dollars in tables; percentages to one decimal place.
MEASURES = {
    "seats": {"chart": "count", "kpi": "count", "table": "count"},
    "recoverable_year": {"chart": "usd_compact", "kpi": "usd_compact", "table": "usd"},
    "unit_cost": {"table": "usd"},
    "share": {"legend": "percent"},
    "days_idle": {"table": "count"},
}

CLASS_LIST = [
    {"id": c, "label": CLASS_LABELS[c], "role": CLASS_ROLES[c], "recoverable": c in RECOVERABLE} for c in CLASSES
]


def _kpi(panel_id: str, title: str, measure_field: str, measure: str, span: int, **extra: Any) -> dict[str, Any]:
    return {
        "id": panel_id,
        "band": "kpis",
        "title": title,
        "mark": "kpi",
        "field": measure_field,
        "measure": measure,
        "format": MEASURES[measure]["kpi"],
        "span": span,
        **extra,
    }


_POLISHED: dict[str, Any] = {
    "id": DASHBOARD_ID,
    "title": "License Optimization",
    "variant": "polished",
    "methodology": "License Optimization",
    "sources": ["License Management System", "SAP"],
    "record": "seat",
    "hierarchy": ["vendor", "product", "class", "seat"],
    "classes": CLASS_LIST,
    "fonts": FONTS,
    "measures": MEASURES,
    "grid": {"columns": GRID_COLUMNS, "gutter": "space-4"},
    "surface": "surface-raised",
    "bands": [
        {"id": "kpis", "title": "Key figures"},
        {"id": "charts", "title": "Charts"},
        {"id": "focus", "title": "Optimisation candidates"},
        {"id": "records", "title": "Seats"},
    ],
    "panels": [
        _kpi("k-entitled", "Entitled", "entitled", "seats", 2, emphasis="primary", rule_role="anomaly"),
        _kpi("k-assigned", "Assigned", "assigned", "seats", 2),
        _kpi("k-active", "Active", "active", "seats", 2),
        _kpi("k-idle", "Unused or underused", "idle", "seats", 3),
        _kpi(
            "k-recoverable",
            "Recoverable a year",
            "recoverable_year",
            "recoverable_year",
            3,
            note={"text": "priced products only, {withheld_seats} seats withheld", "role": "text-secondary"},
        ),
        {
            "id": "seats-treemap",
            "band": "charts",
            "title": "Seats by vendor and product",
            "mark": "treemap",
            "span": 12,
            "height": 360,
            "binding": {"path": ["vendor", "product", "class"], "size": "seats", "colour": "class"},
            "measure": "seats",
            "format": MEASURES["seats"]["chart"],
            "legend": {"items": "classes", "measure": "share", "format": MEASURES["share"]["legend"], "of": "entitled seats"},
            "drill": True,
            "latency_ms": 0,
        },
        {
            "id": "entitlement",
            "band": "charts",
            "title": "Entitled, assigned and active by product",
            "subtitle": "The gap is the finding",
            "mark": "bar",
            "orientation": "horizontal",
            "grouped": True,
            "span": 4,
            "height": 440,
            "category": {"field": "product", "axis": {"name": "Product", "unit": None}},
            "value": {"measure": "seats", "format": MEASURES["seats"]["chart"], "axis": {"name": "Seats", "unit": "seats"}},
            "series": [
                {"id": "entitled", "label": "Entitled", "role": "baseline"},
                {"id": "assigned", "label": "Assigned", "role": "series-1"},
                {"id": "active", "label": "Active", "role": "positive"},
            ],
            "drill": True,
            "latency_ms": 0,
        },
        {
            "id": "trend",
            "band": "charts",
            "title": "Assigned and in use, by month",
            "mark": "line",
            "span": 4,
            "height": 440,
            "category": {"field": "month", "format": "month", "axis": {"name": "Month", "unit": None}},
            "value": {"measure": "seats", "format": MEASURES["seats"]["chart"], "axis": {"name": "Seats", "unit": "seats"}},
            "series": [
                {"id": "assigned", "label": "Assigned", "role": "series-1"},
                {"id": "in_use", "label": "In use", "role": "positive"},
            ],
            "drill": False,
            "latency_ms": 0,
        },
        {
            "id": "recoverable",
            "band": "charts",
            "title": "Recoverable cost by product",
            "subtitle": "A year, priced products; unpriced products are withheld",
            "mark": "bar",
            "orientation": "horizontal",
            "grouped": False,
            "span": 4,
            "height": 440,
            "category": {"field": "product", "axis": {"name": "Product", "unit": None}},
            "value": {
                "measure": "recoverable_year",
                "format": MEASURES["recoverable_year"]["chart"],
                "axis": {"name": "Recoverable a year", "unit": "USD"},
            },
            "series": [{"id": "recoverable_year", "label": "Recoverable a year", "role": "anomaly"}],
            "withheld": {"label": "Withheld", "role": "text-muted"},
            "drill": True,
            "latency_ms": 0,
        },
        {
            "id": "candidates",
            "band": "focus",
            "title": "Optimisation candidates",
            "caption": "Per product, largest recoverable cost first; withheld products by recoverable seats",
            "caption_role": "text-secondary",
            "mark": "table",
            "span": 12,
            "row_key": "product_id",
            "drill": True,
            "total_row": True,
            "columns": [
                {"id": "product", "label": "Product", "format": "text", "drill": True},
                {"id": "vendor", "label": "Vendor", "format": "text"},
                {"id": "entitled", "label": "Entitled", "format": MEASURES["seats"]["table"], "measure": "seats", "align": "end"},
                *[
                    {"id": c, "label": CLASS_LABELS[c], "format": MEASURES["seats"]["table"], "measure": "seats", "align": "end", "class": c}
                    for c in CLASSES
                ],
                {
                    "id": "recoverable_year",
                    "label": "Recoverable a year",
                    "format": MEASURES["recoverable_year"]["table"],
                    "measure": "recoverable_year",
                    "align": "end",
                    "null": "Withheld",
                },
            ],
        },
        {
            "id": "seats",
            "band": "records",
            "title": "Seats",
            "mark": "table",
            "span": 12,
            "row_key": "seat_id",
            "page_size": 25,
            "sortable": True,
            "default_sort": {"column": "seat_id", "direction": "asc"},
            "footer": "class_counts",
            "columns": [
                {"id": "seat_id", "label": "Seat", "format": "id", "font": "id"},
                {"id": "product", "label": "Product", "format": "text"},
                {"id": "department", "label": "Department", "format": "text"},
                {"id": "assignee", "label": "Assignee", "format": "text", "null": "Unassigned"},
                {"id": "last_used", "label": "Last used", "format": "date", "null": "Never"},
                {"id": "days_idle", "label": "Days idle", "format": MEASURES["days_idle"]["table"], "measure": "days_idle", "align": "end"},
                {"id": "utilisation_class", "label": "Class", "format": "class"},
                {"id": "unit_cost", "label": "Unit cost a month", "format": MEASURES["unit_cost"]["table"], "measure": "unit_cost", "align": "end", "null": "No price"},
            ],
        },
    ],
}


def descriptor(iteration: int = 2) -> dict[str, Any]:
    """The dashboard's descriptor for an iteration: the polished variant for iteration 2, and for
    iteration 1 the polished variant with the defect overlay's descriptor patches, which also
    names the scoped stylesheet (D-13, D-60)."""
    if iteration == 1:
        return overlay.apply_descriptor(_POLISHED)
    return copy.deepcopy(_POLISHED)


def panel(desc: dict[str, Any], panel_id: str) -> dict[str, Any]:
    return next(p for p in desc["panels"] if p["id"] == panel_id)
