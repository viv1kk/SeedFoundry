"""The License Optimization datasets (D-30, D-55): every constraint of seed-reuse-notes.md §5.7,
the methodology of the sample music.md and environment.md, and determinism (NFR-1)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import pytest

from seedfoundry.data import CLASSES, DATASETS, RECOVERABLE, classify, dataset, generate
from seedfoundry.data.generate import MONTHS, SNAPSHOT, seed_for
from seedfoundry.sample import sample_files

BACKEND = Path(__file__).resolve().parents[1]


def digest(name: str) -> str:
    return hashlib.sha256(json.dumps(generate(name).rows(), sort_keys=True).encode()).hexdigest()


@pytest.fixture(scope="module", params=DATASETS)
def data(request):
    return dataset(request.param)


# Determinism (NFR-1)


@pytest.mark.parametrize("name", DATASETS)
def test_two_generations_are_identical(name):
    first, second = generate(name), generate(name)
    assert first is not second
    assert first == second
    assert json.dumps(first.rows(), sort_keys=True) == json.dumps(second.rows(), sort_keys=True)


def test_generation_is_the_same_in_other_processes_whatever_the_hash_seed():
    script = "import hashlib, json; from seedfoundry.data import generate; " + "; ".join(
        f"print(hashlib.sha256(json.dumps(generate({name!r}).rows(), sort_keys=True).encode()).hexdigest())" for name in DATASETS
    )
    here = [digest(name) for name in DATASETS]
    for hash_seed in ("0", "1", "12345"):
        env = {**os.environ, "PYTHONHASHSEED": hash_seed, "PYTHONPATH": str(BACKEND)}
        out = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, env=env, cwd=BACKEND, check=True)
        assert out.stdout.split() == here


def test_the_seed_is_a_fixed_constant_per_estate():
    assert seed_for("primary") == int.from_bytes(hashlib.sha256(b"seedfoundry/license-optimization/primary/v1").digest()[:8], "big")
    assert seed_for("primary") != seed_for("alternate")


def test_the_generator_reads_no_clock():
    source = (BACKEND / "seedfoundry" / "data" / "generate.py").read_text(encoding="utf-8")
    assert not re.search(r"\b(?:time|datetime\.now|date\.today|utcnow)\b\s*\(", source)
    assert re.findall(r"\brng\.(\w+)", source) == ["random"] * len(re.findall(r"\brng\.(\w+)", source))


# The record (seed-reuse-notes.md §5.2, environment.md Data Layer)


def test_every_seat_has_the_record_fields(data):
    ids = [s.seat_id for s in data.seats]
    assert len(set(ids)) == len(ids)
    assert all(re.fullmatch(r"LIC-\d{6}", i) for i in ids)
    for seat in data.seats:
        assert seat.product and seat.vendor
        assert len(seat.usage) == 12 and all(0 <= d <= 31 for d in seat.usage)
        assert seat.utilisation_class in CLASSES
        assert seat.unit_cost == data.product(seat.product_id).unit_cost
        assert seat.vendor_id == data.product(seat.product_id).vendor_id  # vendor comes from the product
        if seat.assignee is None:
            assert seat.department is None and seat.assignee_status is None and seat.assigned_from is None
        else:
            assert seat.department in data.departments and seat.assignee_status in ("employed", "left")


def test_twelve_months_end_at_the_snapshot(data):
    assert data.months == MONTHS and len(MONTHS) == 12
    assert data.snapshot_date == SNAPSHOT.isoformat() == "2026-09-30"


def test_last_used_and_days_idle_agree_with_usage(data):
    for seat in data.seats:
        used = [m for m, days in enumerate(seat.usage) if days]
        if seat.last_used is None:
            assert not used and seat.days_idle is None
            continue
        last = date.fromisoformat(seat.last_used)
        assert seat.days_idle == (SNAPSHOT - last).days >= 0
        if used:
            assert last.strftime("%Y-%m") == MONTHS[used[-1]]
            assert last.day >= seat.usage[used[-1]]  # at least that many active days fit before it
        else:
            assert last < date(2025, 10, 1)  # used before the period, not in it


def test_no_use_before_assignment_or_after_leaving(data):
    for seat in data.seats:
        if seat.assigned_from is not None:
            assert not any(seat.usage[: seat.assigned_from])
        else:
            assert not any(seat.usage)


# The methodology (music.md, Opportunity qualification)


def test_every_class_is_derived_by_musics_rules_in_musics_order(data):
    for seat in data.seats:
        days = sum(seat.usage[-3:])
        if seat.assignee is None:
            expected = "unassigned"
        elif seat.assignee_status == "left":
            expected = "leaver"
        elif days == 0:
            expected = "unused"
        elif days <= 11:
            expected = "underused"
        else:
            expected = "active"
        assert seat.utilisation_class == expected == classify(seat.assignee, seat.assignee_status, seat.usage)


def test_a_leaver_is_a_leaver_whatever_the_usage():
    assert classify("A", "left", (20,) * 12) == "leaver"
    assert classify(None, None, (20,) * 12) == "unassigned"
    assert classify("A", "employed", (0,) * 9 + (4, 4, 3)) == "underused"
    assert classify("A", "employed", (0,) * 9 + (4, 4, 4)) == "active"


def test_one_leaver_is_a_leaver_on_every_product(data):
    status = {}
    for seat in data.seats:
        if seat.assignee:
            assert status.setdefault(seat.assignee, seat.assignee_status) == seat.assignee_status


def test_recoverable_cost_is_unit_cost_times_twelve_on_priced_products_only(data):
    for seat in data.seats:
        if seat.utilisation_class not in RECOVERABLE:
            assert seat.recoverable_year == 0
        elif seat.unit_cost is None:
            assert seat.recoverable_year is None  # withheld, never estimated
        else:
            assert seat.recoverable_year == seat.unit_cost * 12


# Constraints so the tests work (seed-reuse-notes.md §5.7)


def test_every_class_is_present_in_the_estate_and_in_most_products(data):
    assert set(Counter(s.utilisation_class for s in data.seats)) == set(CLASSES)
    with_all = [p for p in data.products if {s.utilisation_class for s in data.seats if s.product_id == p.id} == set(CLASSES)]
    assert len(with_all) > len(data.products) / 2


def test_the_primary_has_nine_or_more_priced_products_and_an_unpriced_one():
    primary = dataset("primary")
    priced = [p for p in primary.products if p.priced]
    assert len(priced) >= 9  # V-1's pie then has more than eight slices
    assert len(primary.products) > len(priced)  # withholding shows


def test_both_estates_grade_partial_because_unit_prices_are_incomplete(data):
    # music.md, Confidence assignment: High at 95% of entitled seats on priced products or more.
    priced = sum(1 for s in data.seats if s.unit_cost is not None)
    assert priced / len(data.seats) < 0.95
    assert any(p.unit_cost is None for p in data.products)


def test_two_vendors_or_more_have_several_products(data):
    per_vendor = Counter(p.vendor_id for p in data.products)
    assert sum(1 for n in per_vendor.values() if n > 1) >= 2


def test_ids_are_unique_slugs(data):
    for ids in ([p.id for p in data.products], [v for v, _ in data.vendors]):
        assert len(set(ids)) == len(ids)
        assert all(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", i) for i in ids)


def test_the_alternate_is_a_different_estate_with_the_same_schema():
    primary, alternate = dataset("primary"), dataset("alternate")
    assert {p.vendor for p in primary.products}.isdisjoint(p.vendor for p in alternate.products)
    assert {p.name for p in primary.products}.isdisjoint(p.name for p in alternate.products)
    assert len(primary.seats) != len(alternate.seats) and len(primary.products) != len(alternate.products)
    assert set(primary.departments) != set(alternate.departments)
    assert primary.seats[0].row().keys() == alternate.seats[0].row().keys()
    assert primary.summary().keys() == alternate.summary().keys()


def test_the_primary_departments_are_the_sample_accounts():
    environment = next(content for name, _, content in sample_files() if name == "Environment_01.md")
    named = re.search(r"Departments are named as the firm names them: (.+)\.", environment).group(1)
    assert list(dataset("primary").departments) == [d.strip() for d in named.replace(" and ", ", ").split(",")]


def test_no_em_dash_in_any_value(data):
    assert chr(0x2014) not in json.dumps(data.rows(), ensure_ascii=False)
