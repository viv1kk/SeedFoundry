"""The dashboard payload: every panel's data at one drill level, built from the seat rows by the
query engine (FR-D-4, FR-D-6, D-56). A pure function of the dataset, the descriptor, the drill
path and the Seats table's page and sort, so the same request always gives the same payload
(NFR-1). Values are raw numbers; the descriptor names their format.

A drill target is a step: the level ids that one click on that element appends to the path.
"""

from __future__ import annotations

from typing import Any

from seedfoundry.dashboard.query import Drill, QueryError, group, measures, monthly, parse, select
from seedfoundry.data.model import CLASS_LABELS, CLASSES, Dataset, Seat

SORT_DIRECTIONS = ("asc", "desc")


def _share(count: int, total: int) -> float:
    return round(100 * count / total, 1) if total else 0.0


def _step(drill: Drill, seat: Seat, down_to: str) -> list[str] | None:
    """The ids one click appends to reach `down_to` (vendor, product or class) for this seat's
    branch, or None when the drill is already at or below that level."""
    ids = {"vendor": seat.vendor_id, "product": seat.product_id, "class": seat.utilisation_class}
    order = ["vendor", "product", "class"]
    wanted = order[drill.depth : order.index(down_to) + 1]
    return [ids[kind] for kind in wanted] or None


def kpis(totals: dict[str, int]) -> dict[str, Any]:
    return {
        "k-entitled": {"value": totals["entitled"]},
        "k-assigned": {"value": totals["assigned"]},
        "k-active": {"value": totals["active"]},
        "k-idle": {"value": totals["idle"]},
        "k-recoverable": {
            "value": totals["recoverable_year"],
            "withheld_seats": totals["withheld_seats"],
            "recoverable_seats": totals["recoverable_seats"],
        },
    }


def _ordered(groups: dict[str, list[Seat]], size: dict[str, int]) -> list[str]:
    return sorted(groups, key=lambda key: (-size[key], groups[key][0].vendor, groups[key][0].product))


def treemap(drill: Drill, seats: list[Seat], totals: dict[str, int]) -> dict[str, Any]:
    """Vendor, then product, then class, from the drill's depth down; sized by entitled seats."""

    def classes(branch: list[Seat]) -> list[dict[str, Any]]:
        counts = measures(branch)
        return [
            {
                "id": c,
                "name": CLASS_LABELS[c],
                "level": "class",
                "class": c,
                "value": counts[c],
                "step": _step(drill, next(s for s in branch if s.utilisation_class == c), "class"),
            }
            for c in CLASSES
            if counts[c]
        ]

    def products(branch: list[Seat]) -> list[dict[str, Any]]:
        by_product = group(branch, lambda s: s.product_id)
        sizes = {k: len(v) for k, v in by_product.items()}
        return [
            {
                "id": pid,
                "name": rows[0].product,
                "level": "product",
                "value": len(rows),
                "step": _step(drill, rows[0], "product"),
                "children": classes(rows),
            }
            for pid in _ordered(by_product, sizes)
            for rows in [by_product[pid]]
        ]

    if drill.depth == 0:
        by_vendor = group(seats, lambda s: s.vendor_id)
        sizes = {k: len(v) for k, v in by_vendor.items()}
        nodes = [
            {
                "id": vid,
                "name": rows[0].vendor,
                "level": "vendor",
                "value": len(rows),
                "step": _step(drill, rows[0], "vendor"),
                "children": products(rows),
            }
            for vid in sorted(by_vendor, key=lambda k: (-sizes[k], by_vendor[k][0].vendor))
            for rows in [by_vendor[vid]]
        ]
    elif drill.depth == 1:
        nodes = products(seats)
    else:
        nodes = classes(seats)
    legend = [{"class": c, "label": CLASS_LABELS[c], "count": totals[c], "share": _share(totals[c], totals["entitled"])} for c in CLASSES]
    targets = [{"label": n["name"], "value": n["value"], "step": n["step"]} for n in nodes if n["step"]]
    return {"nodes": nodes, "legend": legend, "total": totals["entitled"], "targets": targets}


def _products(drill: Drill, seats: list[Seat]) -> list[dict[str, Any]]:
    """One entry per product in the filter, with its measures and its drill step."""
    out = []
    for pid, rows in group(seats, lambda s: s.product_id).items():
        counts = measures(rows)
        priced = rows[0].unit_cost is not None
        out.append(
            {
                "id": pid,
                "name": rows[0].product,
                "vendor": rows[0].vendor,
                "vendor_id": rows[0].vendor_id,
                "unit_cost": rows[0].unit_cost,
                "step": _step(drill, rows[0], "product"),
                **counts,
                "recoverable_year": counts["recoverable_year"] if priced else None,
            }
        )
    return out


def _by_priority(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """music.md, Prioritisation: largest recoverable cost a year first; where cost is withheld,
    by recoverable seats. Withheld products follow the priced ones."""
    return sorted(
        products,
        key=lambda p: (p["recoverable_year"] is None, -(p["recoverable_year"] or 0), -p["recoverable_seats"], p["name"]),
    )


def entitlement(products: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(products, key=lambda p: (-p["entitled"], p["name"]))
    return {
        "categories": [{"id": p["id"], "name": p["name"], "vendor": p["vendor"], "step": p["step"]} for p in ordered],
        "series": {key: [p[key] for p in ordered] for key in ("entitled", "assigned", "active")},
        "targets": [{"label": p["name"], "value": p["entitled"], "step": p["step"]} for p in ordered if p["step"]],
    }


def trend(data: Dataset, seats: list[Seat]) -> dict[str, Any]:
    return {"months": list(data.months), "series": monthly(seats, len(data.months))}


def recoverable(products: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = _by_priority(products)
    return {
        "categories": [{"id": p["id"], "name": p["name"], "vendor": p["vendor"], "step": p["step"]} for p in ordered],
        "values": [p["recoverable_year"] for p in ordered],
        "seats": [p["recoverable_seats"] for p in ordered],
        "withheld": [p["recoverable_year"] is None for p in ordered],
        "targets": [
            {"label": p["name"], "value": p["recoverable_year"], "step": p["step"]} for p in ordered if p["step"]
        ],
    }


CANDIDATE_COUNTS = ("entitled", *CLASSES)


def candidates(products: list[dict[str, Any]], totals: dict[str, int]) -> dict[str, Any]:
    rows = [
        {
            "product_id": p["id"],
            "product": p["name"],
            "vendor": p["vendor"],
            "step": p["step"],
            **{key: p[key] for key in CANDIDATE_COUNTS},
            "recoverable_year": p["recoverable_year"],
            "recoverable_seats": p["recoverable_seats"],
        }
        for p in _by_priority(products)
    ]
    total = {
        "product": "Total",
        "vendor": "",
        **{key: totals[key] for key in CANDIDATE_COUNTS},
        "recoverable_year": totals["recoverable_year"],
        "recoverable_seats": totals["recoverable_seats"],
        "withheld_seats": totals["withheld_seats"],
    }
    return {"rows": rows, "total": total}


SEAT_COLUMNS = ("seat_id", "product", "department", "assignee", "last_used", "days_idle", "utilisation_class", "unit_cost")


def _sort_key(column: str):
    if column == "utilisation_class":
        return lambda s: CLASSES.index(s.utilisation_class)
    return lambda s: getattr(s, column)


def seat_rows(desc_panel: dict[str, Any], seats: list[Seat], totals: dict[str, int], page: int, sort: str | None, direction: str | None) -> dict[str, Any]:
    default = desc_panel["default_sort"]
    sort = sort or default["column"]
    direction = direction or default["direction"]
    if sort not in SEAT_COLUMNS:
        raise QueryError(400, "bad_sort", f"Seats cannot be sorted by {sort!r}.")
    if direction not in SORT_DIRECTIONS:
        raise QueryError(400, "bad_sort", f"Sort direction is asc or desc, not {direction!r}.")
    key = _sort_key(sort)
    present = [s for s in seats if getattr(s, sort) is not None]
    missing = [s for s in seats if getattr(s, sort) is None]
    # Seat id breaks ties, so the order is total; empty values go last either way.
    present.sort(key=lambda s: s.seat_id)
    present.sort(key=key, reverse=direction == "desc")
    ordered = present + missing
    size = desc_panel["page_size"]
    pages = max(1, -(-len(ordered) // size))
    page = min(max(1, page), pages)
    rows = [
        {
            "seat_id": s.seat_id,
            "product_id": s.product_id,
            "product": s.product,
            "vendor": s.vendor,
            "department": s.department,
            "assignee": s.assignee,
            "last_used": s.last_used,
            "days_idle": s.days_idle,
            "utilisation_class": s.utilisation_class,
            "unit_cost": s.unit_cost,
        }
        for s in ordered[(page - 1) * size : page * size]
    ]
    footer = {**{c: totals[c] for c in CLASSES}, "total": totals["entitled"]}
    return {
        "rows": rows,
        "page": page,
        "pages": pages,
        "page_size": size,
        "total": len(ordered),
        "first": (page - 1) * size + 1 if rows else 0,
        "last": (page - 1) * size + len(rows),
        "sort": sort,
        "direction": direction,
        "footer": footer,
    }


def build(desc: dict[str, Any], data: Dataset, drill_path: str | None = None, page: int = 1, sort: str | None = None, direction: str | None = None) -> dict[str, Any]:
    """Every panel's data at one drill level, from the seat rows."""
    drill = parse(data, drill_path)
    seats = select(data, drill)
    totals = measures(seats)
    products = _products(drill, seats)
    seats_panel = next(p for p in desc["panels"] if p["id"] == "seats")
    panels: dict[str, Any] = {
        **kpis(totals),
        "seats-treemap": treemap(drill, seats, totals),
        "entitlement": entitlement(products),
        "trend": trend(data, seats),
        "recoverable": recoverable(products),
        "candidates": candidates(products, totals),
        "seats": seat_rows(seats_panel, seats, totals, page, sort, direction),
    }
    return {
        "dashboard": desc["id"],
        "dataset": {
            "name": data.name,
            "title": data.title,
            "snapshot_date": data.snapshot_date,
            "period": {"from": data.months[0], "to": data.months[-1]},
            "seats": len(data.seats),
        },
        "drill": drill.as_data(),
        "panels": {p["id"]: panels[p["id"]] for p in desc["panels"]},
    }
