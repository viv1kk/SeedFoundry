"""The query engine (D-29, D-56): one filter context, the drill path, that every panel follows,
and the aggregations every figure comes from, always over seat rows.

Hierarchy (seed-reuse-notes.md §5.6): all products, vendor, product, utilisation class, seat.
The drill path is a list of steps; a step names one or more levels, because a treemap leaf
drills vendor, product and class in one click and its crumb names all three. In the URL a path
is its steps joined by "/", and a step's level ids joined by ".": "microsoft.microsoft-365-e3.unused"
is one step, "microsoft/microsoft-365-e3/unused" three. Levels are positional: the first id is a
vendor, the second one of its products, the third a class.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from seedfoundry.data.model import CLASS_LABELS, CLASSES, Dataset, Seat

LEVELS = ("vendor", "product", "class")
DEPTH_NAMES = ("all", "vendor", "product", "class")
ROOT_LABEL = "All products"
CRUMB_JOIN = " › "  # single right-pointing angle quotation mark, as Seed v0.1's crumb


class QueryError(ValueError):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


@dataclass(frozen=True)
class Level:
    kind: str  # vendor, product or class
    id: str
    label: str

    def as_data(self) -> dict[str, str]:
        return {"kind": self.kind, "id": self.id, "label": self.label}


@dataclass(frozen=True)
class Drill:
    steps: tuple[tuple[Level, ...], ...] = ()

    @property
    def levels(self) -> tuple[Level, ...]:
        return tuple(level for step in self.steps for level in step)

    def _id(self, kind: str) -> str | None:
        return next((level.id for level in self.levels if level.kind == kind), None)

    @property
    def vendor(self) -> str | None:
        return self._id("vendor")

    @property
    def product(self) -> str | None:
        return self._id("product")

    @property
    def cls(self) -> str | None:
        return self._id("class")

    @property
    def depth(self) -> int:
        return len(self.levels)

    @property
    def level(self) -> str:
        return DEPTH_NAMES[self.depth]

    @property
    def deepest(self) -> bool:
        return self.depth == len(LEVELS)

    @staticmethod
    def step_path(step: tuple[Level, ...]) -> str:
        return ".".join(level.id for level in step)

    @property
    def path(self) -> str:
        return "/".join(self.step_path(step) for step in self.steps)

    def crumbs(self) -> list[dict[str, Any]]:
        crumbs: list[dict[str, Any]] = [{"label": ROOT_LABEL, "path": "", "levels": []}]
        for i, step in enumerate(self.steps):
            crumbs.append(
                {
                    "label": CRUMB_JOIN.join(level.label for level in step),
                    "path": "/".join(self.step_path(s) for s in self.steps[: i + 1]),
                    "levels": [level.as_data() for level in step],
                }
            )
        return crumbs

    def as_data(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "level": self.level,
            "depth": self.depth,
            "deepest": self.deepest,
            "filter": {"vendor": self.vendor, "product": self.product, "class": self.cls},
            "crumbs": self.crumbs(),
        }


def parse(data: Dataset, text: str | None) -> Drill:
    """The drill path from the URL. A path that names nothing in the data is refused (404), so a
    stale or mistyped address never shows a dashboard for a filter that does not exist."""
    if not text:
        return Drill()
    raw_steps = text.split("/")
    if any(not step for step in raw_steps):
        raise QueryError(404, "drill_not_found", f"The drill path {text!r} has an empty step.")
    steps: list[tuple[Level, ...]] = []
    position = 0
    vendor_id: str | None = None
    for raw in raw_steps:
        step: list[Level] = []
        for level_id in raw.split("."):
            if position >= len(LEVELS):
                raise QueryError(404, "drill_not_found", f"The drill path {text!r} goes deeper than vendor, product and class.")
            kind = LEVELS[position]
            step.append(_resolve(data, kind, level_id, vendor_id, text))
            if kind == "vendor":
                vendor_id = level_id
            position += 1
        steps.append(tuple(step))
    return Drill(tuple(steps))


def _resolve(data: Dataset, kind: str, level_id: str, vendor_id: str | None, text: str) -> Level:
    if kind == "vendor":
        name = dict(data.vendors).get(level_id)
        if name is None:
            raise QueryError(404, "drill_not_found", f"No vendor {level_id!r} in the data (drill path {text!r}).")
        return Level(kind, level_id, name)
    if kind == "product":
        product = data.product(level_id)
        if product is None or product.vendor_id != vendor_id:
            raise QueryError(404, "drill_not_found", f"No product {level_id!r} under vendor {vendor_id!r} (drill path {text!r}).")
        return Level(kind, level_id, product.name)
    if level_id not in CLASSES:
        raise QueryError(404, "drill_not_found", f"No utilisation class {level_id!r} (drill path {text!r}).")
    return Level(kind, level_id, CLASS_LABELS[level_id])


def select(data: Dataset, drill: Drill) -> list[Seat]:
    """The seat rows inside the filter, in dataset order."""
    return [
        s
        for s in data.seats
        if (drill.vendor is None or s.vendor_id == drill.vendor)
        and (drill.product is None or s.product_id == drill.product)
        and (drill.cls is None or s.utilisation_class == drill.cls)
    ]


# Aggregations. Every figure on the dashboard is one of these over the selected rows.

COUNT_KEYS = ("entitled", "assigned", *CLASSES, "idle", "recoverable_seats", "withheld_seats")


def measures(seats: Iterable[Seat]) -> dict[str, int]:
    """Counts and recoverable cost over seats. recoverable_year sums priced seats only;
    withheld_seats counts recoverable seats on unpriced products (seed-reuse-notes.md §5.7)."""
    out = dict.fromkeys(COUNT_KEYS, 0)
    out["recoverable_year"] = 0
    for seat in seats:
        out["entitled"] += 1
        out[seat.utilisation_class] += 1
        if seat.utilisation_class != "unassigned":
            out["assigned"] += 1
        if seat.utilisation_class in ("unused", "underused"):
            out["idle"] += 1
        if seat.recoverable:
            out["recoverable_seats"] += 1
            if seat.unit_cost is None:
                out["withheld_seats"] += 1
            else:
                out["recoverable_year"] += seat.unit_cost * 12
    return out


def group(seats: Iterable[Seat], key: Callable[[Seat], str]) -> dict[str, list[Seat]]:
    """Seats grouped by a key, groups in the order their first seat appears."""
    grouped: dict[str, list[Seat]] = {}
    for seat in seats:
        grouped.setdefault(key(seat), []).append(seat)
    return grouped


def monthly(seats: Iterable[Seat], months: int) -> dict[str, list[int]]:
    """Per month: seats assigned in that month, and seats with at least one active day."""
    assigned = [0] * months
    in_use = [0] * months
    for seat in seats:
        start = seat.assigned_from
        for m in range(months):
            if start is not None and start <= m:
                assigned[m] += 1
            if seat.usage[m] > 0:
                in_use[m] += 1
    return {"assigned": assigned, "in_use": in_use}
