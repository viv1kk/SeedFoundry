"""The seeded generator for SeedFoundry's License Optimization estates (D-30, D-55).

Seed rule: each estate's RNG is `random.Random(n)`, where n is the first eight bytes, big-endian,
of sha256("seedfoundry/license-optimization/<estate>/v1"). The seed is a fixed constant per
estate, never the clock or the intake, so every generation of an estate is identical (NFR-1).
Only `Random.random()` is called, whose sequence for a given seed Python keeps stable across
versions (unlike `randrange` and `choice`), and nothing iterates a set or reads a hash, so the
output does not depend on PYTHONHASHSEED either.

Steps: a staff directory (unique names, a department by headcount weight, who left and in which
month, who joined mid-period), then each product in order: its assignees drawn from the
directory by the product's department weights, each holder's monthly use, `last_used` within the
last month with use, and the class by music.md's rules (model.classify).
"""

from __future__ import annotations

import calendar
import hashlib
import random
import re
from dataclasses import dataclass
from datetime import date, timedelta
from functools import cache

from seedfoundry.data.estates import ESTATES, FIRST_NAMES, LAST_NAMES, EstateSpec, ProductSpec
from seedfoundry.data.model import Dataset, Product, Seat, classify

SEED_RULE = 'random.Random(int.from_bytes(sha256("seedfoundry/license-optimization/<estate>/v1")[:8], "big")), random() only'

# Twelve months of monthly usage, October 2025 to September 2026; the snapshot is taken on the
# last day. The firm's year (environment.md) has use dips in August and late December.
FIRST_MONTH = (2025, 10)
MONTH_COUNT = 12
SEASON = {12: 0.7, 8: 0.6}


def month_ids() -> tuple[str, ...]:
    year, month = FIRST_MONTH
    ids = []
    for _ in range(MONTH_COUNT):
        ids.append(f"{year:04d}-{month:02d}")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return tuple(ids)


MONTHS = month_ids()


def month_end(month_id: str) -> date:
    year, month = (int(part) for part in month_id.split("-"))
    return date(year, month, calendar.monthrange(year, month)[1])


SNAPSHOT = month_end(MONTHS[-1])
PERIOD_START = date(*FIRST_MONTH, 1)


def seed_for(estate: str) -> int:
    return int.from_bytes(hashlib.sha256(f"seedfoundry/license-optimization/{estate}/v1".encode()).digest()[:8], "big")


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


class Draw:
    """The estate's random draws, all from Random.random()."""

    def __init__(self, seed: int) -> None:
        self.rng = random.Random(seed)

    def chance(self, p: float) -> bool:
        return self.rng.random() < p

    def between(self, low: int, high: int) -> int:
        """An integer in [low, high]."""
        return low + int(self.rng.random() * (high - low + 1))

    def weighted(self, weights: dict[str, float]) -> str:
        names = list(weights)
        point = self.rng.random() * sum(weights.values())
        for name in names:
            point -= weights[name]
            if point < 0:
                return name
        return names[-1]


@dataclass(frozen=True)
class Person:
    index: int
    name: str
    department: str
    left_month: int | None  # first month without use, for someone who has left
    join_month: int  # first month with the seat; 0 for someone there all year


def directory(spec: EstateSpec, draw: Draw) -> list[Person]:
    names = [f"{first} {last}" for first in FIRST_NAMES for last in LAST_NAMES]
    if spec.people > len(names):
        raise ValueError(f"{spec.name}: {spec.people} people but only {len(names)} distinct names")
    # A partial Fisher-Yates shuffle: the first `people` names, each used once.
    for i in range(spec.people):
        j = draw.between(i, len(names) - 1)
        names[i], names[j] = names[j], names[i]
    people = []
    for i in range(spec.people):
        department = draw.weighted(spec.departments)
        left = draw.between(3, MONTH_COUNT - 1) if draw.chance(spec.leaver_rate) else None
        joined = draw.between(1, MONTH_COUNT - 1) if left is None and draw.chance(spec.joiner_rate) else 0
        people.append(Person(i, names[i], department, left, joined))
    return people


def holders(spec: ProductSpec, estate: EstateSpec, people: list[Person], count: int, draw: Draw) -> list[Person]:
    """`count` distinct people, drawn by department weight (Efraimidis and Spirakis), in directory order."""
    weights = spec.departments or estate.departments
    keyed = []
    for person in people:
        u = draw.rng.random()
        weight = weights.get(person.department, 0)
        if weight > 0:
            keyed.append((u ** (1 / weight), person.index))
    if len(keyed) < count:
        raise ValueError(f"{spec.name}: {count} holders wanted, {len(keyed)} people in its departments")
    chosen = sorted(keyed, key=lambda pair: (-pair[0], pair[1]))[:count]
    return [people[index] for _, index in sorted(chosen, key=lambda pair: pair[1])]


def regular_days(month: int, draw: Draw) -> int:
    calendar_month = int(MONTHS[month].split("-")[1])
    return max(1, round(draw.between(6, 20) * SEASON.get(calendar_month, 1.0)))


def usage_for(person: Person, spec: ProductSpec, draw: Draw) -> tuple[int, ...]:
    """Days active in each month for one holder."""
    roll = draw.rng.random()
    behaviour = "idle" if roll < spec.idle else "occasional" if roll < spec.idle + spec.occasional else "regular"
    stop = MONTH_COUNT
    if behaviour == "idle":
        # Use that stopped before the last three months, or never started.
        stop = draw.between(person.join_month, 8) if draw.chance(0.7) and person.join_month <= 8 else person.join_month
    end = min(stop, person.left_month if person.left_month is not None else MONTH_COUNT)
    days = []
    for month in range(MONTH_COUNT):
        if month < person.join_month or month >= end:
            days.append(0)
        elif behaviour == "occasional":
            days.append(draw.between(1, 3) if draw.chance(0.45) else 0)
        else:
            days.append(regular_days(month, draw))
    return tuple(days)


def last_use(usage: tuple[int, ...], draw: Draw) -> date | None:
    """A day in the last month with use, no earlier than its count of active days. Without use in
    the period, a date before it for some holders, and never for the rest."""
    for month in range(MONTH_COUNT - 1, -1, -1):
        if usage[month]:
            end = month_end(MONTHS[month])
            return end.replace(day=draw.between(min(usage[month], end.day), end.day))
    if draw.chance(0.5):
        return PERIOD_START - timedelta(days=draw.between(1, 300))
    return None


def generate(name: str) -> Dataset:
    """Build an estate from its spec. Pure: the same name gives the same dataset every time."""
    spec = ESTATES[name]
    draw = Draw(seed_for(name))
    people = directory(spec, draw)
    products: list[Product] = []
    seats: list[Seat] = []
    for product_spec in spec.products:
        product = Product(slug(product_spec.name), product_spec.name, slug(product_spec.vendor), product_spec.vendor, product_spec.unit_cost)
        products.append(product)
        assigned = product_spec.seats - round(product_spec.seats * product_spec.unassigned)
        held = holders(product_spec, spec, people, assigned, draw)
        for person in held + [None] * (product_spec.seats - assigned):
            usage = usage_for(person, product_spec, draw) if person else (0,) * MONTH_COUNT
            last = last_use(usage, draw) if person else None
            status = None if person is None else "left" if person.left_month is not None else "employed"
            assignee = person.name if person else None
            seats.append(
                Seat(
                    seat_id=f"LIC-{len(seats) + 1:06d}",
                    product_id=product.id,
                    product=product.name,
                    vendor_id=product.vendor_id,
                    vendor=product.vendor,
                    department=person.department if person else None,
                    assignee=assignee,
                    assignee_status=status,
                    assigned_from=person.join_month if person else None,
                    usage=usage,
                    last_used=last.isoformat() if last else None,
                    days_idle=(SNAPSHOT - last).days if last else None,
                    utilisation_class=classify(assignee, status, usage),
                    unit_cost=product.unit_cost,
                )
            )
    return Dataset(
        name=spec.name,
        title=spec.title,
        description=spec.description,
        seed_rule=SEED_RULE,
        snapshot_date=SNAPSHOT.isoformat(),
        months=MONTHS,
        departments=tuple(spec.departments),
        products=tuple(products),
        seats=tuple(seats),
    )


@cache
def dataset(name: str) -> Dataset:
    """The estate, generated once per process (generation is pure, so caching changes nothing)."""
    return generate(name)


DATASETS = tuple(ESTATES)
