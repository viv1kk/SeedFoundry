"""Numeric reconciliation (T-16, FR-T-3, build-simulation.md §6.2): recompute every figure in a
dashboard payload from the seat rows and compare it with what the payload shows.

The recount is written here on purpose, with its own loops over the rows, and does not call the
query engine that built the payload: a check that reused the engine's code would agree with any
mistake in it. Checks: derived KPIs equal their formula; part sums equal their totals; the
treemap legend's shares sum to 100 within 0.1; table totals equal their row sums; the same
measure agrees on every panel where it appears; every figure equals its recount.

Minimal in M7 (the exit criterion: the polished payload passes); M9 maps each problem to a
finding (N-1 to N-5).
"""

from __future__ import annotations

from typing import Any

from seedfoundry.data.model import Dataset, Seat
from seedfoundry.validators.problems import Problem

CLASS_IDS = ("active", "underused", "unused", "leaver", "unassigned")
RECOVERABLE_IDS = ("unused", "leaver", "unassigned")
SHARE_TOLERANCE = 0.1


def _rows(data: Dataset, filter_: dict[str, str | None]) -> list[Seat]:
    rows = []
    for seat in data.seats:
        if filter_.get("vendor") and seat.vendor_id != filter_["vendor"]:
            continue
        if filter_.get("product") and seat.product_id != filter_["product"]:
            continue
        if filter_.get("class") and seat.utilisation_class != filter_["class"]:
            continue
        rows.append(seat)
    return rows


def _recount(rows: list[Seat]) -> dict[str, int]:
    counts = {c: 0 for c in CLASS_IDS}
    recoverable_year = withheld = 0
    for seat in rows:
        counts[seat.utilisation_class] += 1
        if seat.utilisation_class in RECOVERABLE_IDS:
            if seat.unit_cost is None:
                withheld += 1
            else:
                recoverable_year += 12 * seat.unit_cost
    return {
        **counts,
        "entitled": len(rows),
        "assigned": sum(1 for s in rows if s.assignee),
        "idle": counts["unused"] + counts["underused"],
        "recoverable_year": recoverable_year,
        "withheld_seats": withheld,
    }


class _Checker:
    def __init__(self) -> None:
        self.problems: list[Problem] = []

    def equal(self, check: str, panel: str, expected: Any, shown: Any, what: str) -> None:
        if expected != shown:
            self.problems.append(Problem("T-16", check, panel, expected, shown, f"{what}: expected {expected}, shown {shown}"))

    def agree(self, what: str, truth: Any, *shown: tuple[str, Any]) -> None:
        """The same measure on two panels. When they disagree, the panel whose figure is off its
        recount is the one reported (both, if both are), so a wrong KPI is not blamed on the
        table beside it (D-60)."""
        values = [value for _, value in shown]
        if all(value == values[0] for value in values):
            return
        for panel, value in [(p, v) for p, v in shown if v != truth] or shown[-1:]:
            self.problems.append(Problem("T-16", "cross-panel", panel, truth, value, f"{what}: the recount is {truth}, {panel} shows {value}"))


def reconcile(payload: dict[str, Any], data: Dataset) -> list[Problem]:
    """Every problem found in the payload; none for a correct one."""
    check = _Checker()
    panels = payload["panels"]
    rows = _rows(data, payload["drill"]["filter"])
    truth = _recount(rows)
    by_product: dict[str, list[Seat]] = {}
    for seat in rows:
        by_product.setdefault(seat.product_id, []).append(seat)

    # KPIs: each equals its formula over the rows.
    for panel_id, key in (("k-entitled", "entitled"), ("k-assigned", "assigned"), ("k-active", "active"), ("k-idle", "idle")):
        check.equal("kpi-formula", panel_id, truth[key], panels[panel_id]["value"], f"{panel_id} value")
    recoverable_kpi = panels["k-recoverable"]
    check.equal("kpi-formula", "k-recoverable", truth["recoverable_year"], recoverable_kpi["value"], "Recoverable a year")
    check.equal("kpi-formula", "k-recoverable", truth["withheld_seats"], recoverable_kpi["withheld_seats"], "Withheld seats")

    # Entitled, assigned and active by product: each bar equals its recount; bars sum to the KPIs.
    entitlement = panels["entitlement"]
    for i, category in enumerate(entitlement["categories"]):
        product_rows = by_product.get(category["id"], [])
        product_truth = _recount(product_rows)
        for key in ("entitled", "assigned", "active"):
            check.equal("figure", "entitlement", product_truth[key], entitlement["series"][key][i], f"{category['name']} {key}")
    check.equal("product-coverage", "entitlement", sorted(by_product), sorted(c["id"] for c in entitlement["categories"]), "products shown")
    for key, kpi in (("entitled", "k-entitled"), ("assigned", "k-assigned"), ("active", "k-active")):
        check.equal("part-sum", "entitlement", panels[kpi]["value"], sum(entitlement["series"][key]), f"{key} bars against the {kpi} KPI")

    # Treemap: leaves equal their recount, children sum to their parent, the total is the KPI.
    treemap = panels["seats-treemap"]
    cells: dict[tuple[tuple[str, str], ...], int] = {}
    for seat in rows:
        path: tuple[tuple[str, str], ...] = ()
        for level, value in (("vendor", seat.vendor_id), ("product", seat.product_id), ("class", seat.utilisation_class)):
            path += ((level, value),)
            cells[path] = cells.get(path, 0) + 1

    def count(scope: dict[str, str]) -> int:
        # The filter's own levels are fixed, so a cell's count is keyed by the full path to it.
        fixed = {**{k: v for k, v in payload["drill"]["filter"].items() if v}, **scope}
        path = tuple((level, fixed[level]) for level in ("vendor", "product", "class") if level in fixed)
        return cells.get(path, 0)

    def walk(nodes: list[dict[str, Any]], scope: dict[str, str]) -> int:
        total = 0
        for node in nodes:
            inner = {**scope, node["level"]: node["id"]}
            if node.get("children"):
                check.equal("part-sum", "seats-treemap", node["value"], walk(node["children"], inner), f"children of {node['name']}")
            check.equal("figure", "seats-treemap", count(inner), node["value"], f"{node['name']} seats")
            total += node["value"]
        return total

    check.equal("part-sum", "seats-treemap", panels["k-entitled"]["value"], walk(treemap["nodes"], {}), "treemap cells against the Entitled KPI")

    # Treemap legend: shares of entitled seats, one decimal each, summing to 100.
    legend = treemap["legend"]
    shares = sum(item["share"] for item in legend)
    if truth["entitled"] and round(abs(shares - 100), 6) > SHARE_TOLERANCE:
        check.problems.append(Problem("T-16", "percent-sum", "seats-treemap", 100.0, round(shares, 1), f"legend shares sum to {shares:.1f}%, not 100%"))
    for item in legend:
        expected_share = round(100 * truth[item["class"]] / truth["entitled"], 1) if truth["entitled"] else 0.0
        check.equal("figure", "seats-treemap", truth[item["class"]], item["count"], f"legend {item['label']} count")
        if round(abs(expected_share - item["share"]), 6) > SHARE_TOLERANCE:
            check.problems.append(Problem("T-16", "figure", "seats-treemap", expected_share, item["share"], f"legend {item['label']} share"))

    # Assigned and in use, by month.
    trend = panels["trend"]
    months = len(data.months)
    assigned = [sum(1 for s in rows if s.assigned_from is not None and s.assigned_from <= m) for m in range(months)]
    in_use = [sum(1 for s in rows if s.usage[m] > 0) for m in range(months)]
    check.equal("figure", "trend", list(data.months), trend["months"], "months")
    check.equal("figure", "trend", assigned, trend["series"]["assigned"], "assigned by month")
    check.equal("figure", "trend", in_use, trend["series"]["in_use"], "in use by month")
    check.agree("assigned in the last month against the Assigned KPI", truth["assigned"], ("k-assigned", panels["k-assigned"]["value"]), ("trend", trend["series"]["assigned"][-1]))

    # Recoverable cost by product: each bar equals unit cost x 12 over its recoverable seats, or is
    # withheld when the product has no price; the priced bars sum to the KPI.
    recoverable = panels["recoverable"]
    for i, category in enumerate(recoverable["categories"]):
        product_truth = _recount(by_product.get(category["id"], []))
        priced = data.product(category["id"]).unit_cost is not None  # type: ignore[union-attr]
        expected = product_truth["recoverable_year"] if priced else None
        check.equal("figure", "recoverable", expected, recoverable["values"][i], f"{category['name']} recoverable a year")
        check.equal("figure", "recoverable", not priced, recoverable["withheld"][i], f"{category['name']} withheld")
    priced_sum = sum(v for v in recoverable["values"] if v is not None)
    check.agree("Recoverable a year against the sum of recoverable cost by product", truth["recoverable_year"], ("recoverable", priced_sum), ("k-recoverable", recoverable_kpi["value"]))

    # Optimisation candidates: rows equal their recount; the total row equals the row sums.
    candidates = panels["candidates"]
    columns = ("entitled", *CLASS_IDS)
    for row in candidates["rows"]:
        product_truth = _recount(by_product.get(row["product_id"], []))
        for key in columns:
            check.equal("figure", "candidates", product_truth[key], row[key], f"{row['product']} {key}")
    for key in columns:
        check.equal("table-total", "candidates", sum(row[key] for row in candidates["rows"]), candidates["total"][key], f"total {key}")
    check.equal(
        "table-total",
        "candidates",
        sum(row["recoverable_year"] or 0 for row in candidates["rows"]),
        candidates["total"]["recoverable_year"],
        "total recoverable a year",
    )
    check.agree("total entitled against the Entitled KPI", truth["entitled"], ("k-entitled", panels["k-entitled"]["value"]), ("candidates", candidates["total"]["entitled"]))
    check.agree("total recoverable against the KPI", truth["recoverable_year"], ("k-recoverable", recoverable_kpi["value"]), ("candidates", candidates["total"]["recoverable_year"]))

    # Seats: the footer's class counts sum to its total, which is the Entitled KPI.
    seats = panels["seats"]
    footer = seats["footer"]
    check.equal("table-total", "seats", sum(footer[c] for c in CLASS_IDS), footer["total"], "footer class counts against the footer total")
    check.agree("footer total against the Entitled KPI", truth["entitled"], ("k-entitled", panels["k-entitled"]["value"]), ("seats", footer["total"]))
    for c in CLASS_IDS:
        check.equal("figure", "seats", truth[c], footer[c], f"footer {c}")
    check.equal("figure", "seats", truth["entitled"], seats["total"], "seat rows in the filter")
    on_page = min(seats["page_size"], max(0, seats["total"] - (seats["page"] - 1) * seats["page_size"]))
    check.equal("figure", "seats", on_page, len(seats["rows"]), "rows on the page")
    by_id = {s.seat_id: s for s in rows}
    for row in seats["rows"]:
        seat = by_id.get(row["seat_id"])
        if seat is None:
            check.problems.append(Problem("T-16", "figure", "seats", "a seat in the filter", row["seat_id"], f"{row['seat_id']} is not in the filter"))
            continue
        for key in ("product", "department", "assignee", "last_used", "days_idle", "utilisation_class", "unit_cost"):
            check.equal("figure", "seats", getattr(seat, key), row[key], f"{row['seat_id']} {key}")

    return check.problems
