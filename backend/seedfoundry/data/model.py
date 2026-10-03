"""The License Optimization record and methodology (seed-reuse-notes.md §5.2 and §5.7, D-30).

A record is a seat. Its utilisation class is derived from the seat, never stored by hand:
the classes are tested in the order the sample music.md gives (Unassigned, Leaver, Unused,
Underused, Active), over "the last 90 days", which the sample environment.md reads as the
three most recent monthly usage records. Recoverable classes are Unused, Leaver and
Unassigned; Underused is reported, never recovered. Cost is unit cost per seat-month x 12,
stated for priced products only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Display order and chart roles (seed-reuse-notes.md §5.2).
CLASSES = ("active", "underused", "unused", "leaver", "unassigned")
CLASS_LABELS = {
    "active": "Active",
    "underused": "Underused",
    "unused": "Unused",
    "leaver": "Leaver",
    "unassigned": "Unassigned",
}
CLASS_ROLES = {
    "active": "positive",
    "underused": "warning",
    "unused": "anomaly",
    "leaver": "negative",
    "unassigned": "muted",
}
RECOVERABLE = ("unused", "leaver", "unassigned")

# music.md, Opportunity qualification: the order the classes are tested in.
TEST_ORDER = ("unassigned", "leaver", "unused", "underused", "active")
ACTIVE_DAYS = 12  # Active: 12 days or more in the last 90 days; Underused: 1 to 11
WINDOW_MONTHS = 3  # environment.md: the last 90 days are the three most recent months

MONTHS_IN_YEAR = 12


def classify(assignee: str | None, assignee_status: str | None, usage: tuple[int, ...]) -> str:
    """The seat's utilisation class, by music.md's rules in music.md's order."""
    if not assignee:
        return "unassigned"
    if assignee_status == "left":
        return "leaver"
    days = sum(usage[-WINDOW_MONTHS:])
    if days == 0:
        return "unused"
    if days < ACTIVE_DAYS:
        return "underused"
    return "active"


@dataclass(frozen=True)
class Product:
    id: str
    name: str
    vendor_id: str
    vendor: str
    unit_cost: int | None  # USD per seat-month; None where the contract states no price

    @property
    def priced(self) -> bool:
        return self.unit_cost is not None

    def row(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "vendor_id": self.vendor_id, "vendor": self.vendor, "unit_cost": self.unit_cost}


@dataclass(frozen=True)
class Seat:
    seat_id: str
    product_id: str
    product: str
    vendor_id: str
    vendor: str
    department: str | None
    assignee: str | None
    assignee_status: str | None  # employed or left; None when unassigned
    assigned_from: int | None  # index of the first month the seat was assigned; None when unassigned
    usage: tuple[int, ...]  # days active in each of the twelve months, oldest first
    last_used: str | None  # ISO date of the last recorded use; None if never used
    days_idle: int | None  # days from last_used to the snapshot date
    utilisation_class: str
    unit_cost: int | None

    @property
    def recoverable(self) -> bool:
        return self.utilisation_class in RECOVERABLE

    @property
    def recoverable_year(self) -> int | None:
        """Unit cost x 12 for a recoverable seat on a priced product; 0 when not recoverable;
        None when recoverable but unpriced (withheld, never estimated)."""
        if not self.recoverable:
            return 0
        return None if self.unit_cost is None else self.unit_cost * MONTHS_IN_YEAR

    def row(self) -> dict[str, Any]:
        return {
            "seat_id": self.seat_id,
            "product_id": self.product_id,
            "product": self.product,
            "vendor_id": self.vendor_id,
            "vendor": self.vendor,
            "department": self.department,
            "assignee": self.assignee,
            "assignee_status": self.assignee_status,
            "assigned_from": self.assigned_from,
            "usage": list(self.usage),
            "last_used": self.last_used,
            "days_idle": self.days_idle,
            "utilisation_class": self.utilisation_class,
            "unit_cost": self.unit_cost,
        }


@dataclass(frozen=True)
class Dataset:
    name: str
    title: str
    description: str
    seed_rule: str
    snapshot_date: str
    months: tuple[str, ...]  # "2025-10" to "2026-09", oldest first
    departments: tuple[str, ...]
    products: tuple[Product, ...]
    seats: tuple[Seat, ...]

    def product(self, product_id: str) -> Product | None:
        return next((p for p in self.products if p.id == product_id), None)

    @property
    def vendors(self) -> list[tuple[str, str]]:
        """(id, name) of each vendor, in the order its first product appears."""
        seen: dict[str, str] = {}
        for p in self.products:
            seen.setdefault(p.vendor_id, p.vendor)
        return list(seen.items())

    def summary(self) -> dict[str, Any]:
        priced = sum(1 for s in self.seats if s.unit_cost is not None)
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "seed_rule": self.seed_rule,
            "snapshot_date": self.snapshot_date,
            "months": list(self.months),
            "departments": list(self.departments),
            "seats": len(self.seats),
            "products": len(self.products),
            "vendors": len(self.vendors),
            "priced_products": sum(1 for p in self.products if p.priced),
            "priced_seat_share": round(100 * priced / len(self.seats), 1) if self.seats else 0.0,
        }

    def rows(self) -> dict[str, Any]:
        """The whole dataset as JSON rows, for inspection (GET /api/datasets/{name})."""
        return {**self.summary(), "product_rows": [p.row() for p in self.products], "seat_rows": [s.row() for s in self.seats]}
