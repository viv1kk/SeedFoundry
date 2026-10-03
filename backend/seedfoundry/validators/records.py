"""Malformed input probes (T-14, FR-T-5, D-62): real checks fed malformed inputs.

Two inputs reach the License Optimization Seed from outside: seat records (environment.md's Data
Layer: the seat record and its twelve months of usage) and drill paths (the address the dashboard
reads, D-56). `check` is the seat record contract: every field present and of its kind, a seat id
of `LIC-` and six digits, a product the estate has with its own name, vendor and unit price, an
assignee status that agrees with the assignee, one usage count per month of the period, each a
number of days a month can hold, a date that exists, and the utilisation class that music.md's
rules give for the record. Drill paths go through the query engine's own parser
(`dashboard.query.parse`), which refuses a path the data does not have.

The probe feeds the contract every row of the estate (all must be accepted) and malformed copies of
one real row, each with one thing wrong (all must be refused), then feeds the parser well-formed
and malformed paths. It fails when a malformed input is accepted, warns when a well-formed one is
refused, and passes otherwise.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any

from seedfoundry.dashboard.query import QueryError, parse
from seedfoundry.data.model import CLASSES, Dataset, classify

FIELDS = (
    "seat_id",
    "product_id",
    "product",
    "vendor_id",
    "vendor",
    "department",
    "assignee",
    "assignee_status",
    "assigned_from",
    "usage",
    "last_used",
    "days_idle",
    "utilisation_class",
    "unit_cost",
)
SEAT_ID = re.compile(r"LIC-\d{6}")
STATUSES = ("employed", "left")
MAX_DAYS = 31


def _date(value: Any) -> bool:
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError):
        return False
    return True


def _count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def check(row: dict[str, Any], data: Dataset) -> list[str]:
    """Why the row breaks the seat record contract; empty for a well-formed row."""
    missing = [f for f in FIELDS if f not in row]
    if missing:
        return [f"missing {', '.join(missing)}"]
    problems: list[str] = []
    if not isinstance(row["seat_id"], str) or not SEAT_ID.fullmatch(row["seat_id"]):
        problems.append(f"seat id {row['seat_id']!r} is not LIC- and six digits")
    product = data.product(row["product_id"]) if isinstance(row["product_id"], str) else None
    if product is None:
        problems.append(f"no product {row['product_id']!r} in the estate")
    else:
        if (row["product"], row["vendor_id"], row["vendor"]) != (product.name, product.vendor_id, product.vendor):
            problems.append(f"product and vendor do not match {product.name} by {product.vendor}")
        if row["unit_cost"] != product.unit_cost:
            problems.append(f"unit cost {row['unit_cost']!r} is not the product's ({product.unit_cost!r})")
    if row["unit_cost"] is not None and not _count(row["unit_cost"]):
        problems.append(f"unit cost {row['unit_cost']!r} is not a price")
    assigned = bool(row["assignee"])
    if assigned and row["assignee_status"] not in STATUSES:
        problems.append(f"assignee status {row['assignee_status']!r} is not employed or left")
    if not assigned and (row["assignee_status"] is not None or row["department"] is not None):
        problems.append("an unassigned seat has an assignee status or a department")
    usage = row["usage"]
    if not isinstance(usage, list) or len(usage) != len(data.months):
        problems.append(f"usage is not one count for each of the {len(data.months)} months")
        usage = None
    elif not all(_count(days) and days <= MAX_DAYS for days in usage):
        problems.append(f"usage holds a count that is not 0 to {MAX_DAYS} days")
        usage = None
    if row["last_used"] is not None and not _date(row["last_used"]):
        problems.append(f"last used {row['last_used']!r} is not a date")
    if row["days_idle"] is not None and not _count(row["days_idle"]):
        problems.append(f"days idle {row['days_idle']!r} is not a count of days")
    if row["utilisation_class"] not in CLASSES:
        problems.append(f"class {row['utilisation_class']!r} is not one of the five")
    elif usage is not None:
        derived = classify(row["assignee"], row["assignee_status"], tuple(usage))
        if derived != row["utilisation_class"]:
            problems.append(f"class {row['utilisation_class']} does not follow from the record ({derived} by music.md's rules)")
    return problems


@dataclass(frozen=True)
class Malformed:
    what: str
    change: dict[str, Any]
    drop: str | None = None


def malformed(row: dict[str, Any]) -> list[Malformed]:
    """Copies of one well-formed row, each with one thing wrong."""
    other = next(c for c in CLASSES if c != row["utilisation_class"] and c != "unassigned")
    return [
        Malformed("a seat id that is not LIC- and six digits", {"seat_id": "LIC-12"}),
        Malformed("a product the estate does not have", {"product_id": "no-such-product"}),
        Malformed("a class that is not one of the five", {"utilisation_class": "dormant"}),
        Malformed("a class the usage does not give", {"utilisation_class": other}),
        Malformed("eleven months of usage", {"usage": row["usage"][:-1]}),
        Malformed("a month of 40 days", {"usage": [40, *row["usage"][1:]]}),
        Malformed("a negative unit cost", {"unit_cost": -36}),
        Malformed("an assignee status that is not employed or left", {"assignee_status": "retired"}),
        Malformed("a last-used date that does not exist", {"last_used": "2026-13-45"}),
        Malformed("negative days idle", {"days_idle": -5}),
        Malformed("no product field", {}, drop="product"),
    ]


def paths(data: Dataset) -> tuple[list[str], list[str]]:
    """Well-formed and malformed drill paths, built on the estate's first product."""
    product = data.products[0]
    vendor, item = product.vendor_id, product.id
    good = ["", vendor, f"{vendor}.{item}.unused"]
    bad = [
        "no-such-vendor",
        f"{vendor}/no-such-product",
        f"{vendor}//unused",
        f"{vendor}/{item}/dormant",
        f"{vendor}/{item}/unused/extra",
    ]
    return good, bad


@dataclass
class Result:
    rows_accepted: int
    rows: int
    refused_good_rows: list[str]
    rejected: list[tuple[str, str]]  # (what, first reason)
    accepted_bad: list[str]
    paths_accepted: list[str]
    paths_refused_good: list[str]
    paths_rejected: list[str]
    paths_accepted_bad: list[str]

    @property
    def malformed(self) -> int:
        return len(self.rejected) + len(self.accepted_bad) + len(self.paths_rejected) + len(self.paths_accepted_bad)

    @property
    def refused(self) -> int:
        return len(self.rejected) + len(self.paths_rejected)

    @property
    def status(self) -> str:
        if self.accepted_bad or self.paths_accepted_bad:
            return "fail"
        if self.refused_good_rows or self.paths_refused_good:
            return "warn"
        return "pass"


def run(data: Dataset) -> Result:
    good = [s.row() for s in data.seats]
    refused_good = [row["seat_id"] for row in good if check(row, data)]
    sample = next(row for row in good if row["assignee"])
    rejected, accepted_bad = [], []
    for case in malformed(sample):
        row = {k: v for k, v in {**sample, **case.change}.items() if k != case.drop}
        reasons = check(row, data)
        if reasons:
            rejected.append((case.what, reasons[0]))
        else:
            accepted_bad.append(case.what)

    def parses(path: str) -> bool:
        try:
            parse(data, path)
        except QueryError:
            return False
        return True

    well_formed, malformed_paths = paths(data)
    good_paths = [p for p in well_formed if parses(p)]
    bad_paths = [p for p in malformed_paths if parses(p)]
    return Result(
        rows_accepted=len(good) - len(refused_good),
        rows=len(good),
        refused_good_rows=refused_good,
        rejected=rejected,
        accepted_bad=accepted_bad,
        paths_accepted=good_paths,
        paths_refused_good=[p for p in well_formed if p not in good_paths],
        paths_rejected=[p for p in malformed_paths if p not in bad_paths],
        paths_accepted_bad=bad_paths,
    )
