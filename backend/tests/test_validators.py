"""The validators (D-57, D-60): numeric reconciliation (T-16) and visual QA (T-17 to T-20) pass on
the polished dashboard, and each rule catches a break of the kind iteration 1's overlay plants. The
structure check behind T-08 (D-58) is here too."""

from __future__ import annotations

import copy

import pytest

from seedfoundry.dashboard import build, descriptor
from seedfoundry.data import dataset
from seedfoundry.validators import numeric, structure, tokens, visual

from test_dashboard import every_drill_path

PRIMARY = dataset("primary")
DESC = descriptor(2)


def panel(desc, panel_id):
    return next(p for p in desc["panels"] if p["id"] == panel_id)


@pytest.fixture(scope="module")
def root():
    return build(DESC, PRIMARY, "")


def checks(problems) -> set[tuple[str, str, str]]:
    return {(p.test, p.check, p.panel) for p in problems}


# The polished dashboard is clean (M7 exit criterion)


@pytest.mark.parametrize("name", ["primary", "alternate"])
def test_numeric_reconciliation_passes_on_the_polished_payload(name):
    data = dataset(name)
    assert numeric.reconcile(build(DESC, data, ""), data) == []


def test_numeric_reconciliation_passes_at_every_drill_level():
    for path in every_drill_path(PRIMARY):
        assert numeric.reconcile(build(DESC, PRIMARY, path), PRIMARY) == [], path


def test_numeric_reconciliation_passes_on_any_page_and_sort():
    for page, sort, direction in ((2, None, None), (40, "days_idle", "desc"), (1, "unit_cost", "asc"), (3, "assignee", "desc")):
        assert numeric.reconcile(build(DESC, PRIMARY, "microsoft", page, sort, direction), PRIMARY) == []


@pytest.mark.parametrize("iteration", [2])
def test_visual_qa_passes_on_the_polished_descriptor(iteration, root):
    assert visual.check(descriptor(iteration), root) == []


# Numeric rules catch each kind of break (N-1 to N-5 in M8)


def test_bars_that_do_not_sum_to_the_kpi_are_caught(root):
    broken = copy.deepcopy(root)
    broken["panels"]["entitlement"]["series"]["entitled"] = [round(v * 1.2) for v in broken["panels"]["entitlement"]["series"]["entitled"]]
    found = checks(numeric.reconcile(broken, PRIMARY))
    assert ("T-16", "part-sum", "entitlement") in found and ("T-16", "figure", "entitlement") in found


def test_shares_that_do_not_sum_to_100_are_caught(root):
    broken = copy.deepcopy(root)
    for item in broken["panels"]["seats-treemap"]["legend"]:
        item["share"] = round(item["share"] * 1.12, 1)
    assert ("T-16", "percent-sum", "seats-treemap") in checks(numeric.reconcile(broken, PRIMARY))


def test_a_kpi_off_its_formula_and_the_cost_panel_is_caught(root):
    broken = copy.deepcopy(root)
    wrong = sum(12 * s.unit_cost for s in PRIMARY.seats if s.utilisation_class in ("unused", "underused") and s.unit_cost is not None)
    broken["panels"]["k-recoverable"]["value"] = wrong
    found = checks(numeric.reconcile(broken, PRIMARY))
    assert ("T-16", "kpi-formula", "k-recoverable") in found and ("T-16", "cross-panel", "k-recoverable") in found


def test_a_footer_total_that_is_not_the_class_sum_is_caught(root):
    broken = copy.deepcopy(root)
    broken["panels"]["seats"]["footer"]["total"] = root["panels"]["k-assigned"]["value"]
    assert ("T-16", "table-total", "seats") in checks(numeric.reconcile(broken, PRIMARY))


def test_a_total_row_that_counts_a_row_twice_is_caught(root):
    broken = copy.deepcopy(root)
    largest = max(broken["panels"]["candidates"]["rows"], key=lambda r: r["entitled"])
    for key in ("entitled", "active", "underused", "unused", "leaver", "unassigned"):
        broken["panels"]["candidates"]["total"][key] += largest[key]
    assert ("T-16", "table-total", "candidates") in checks(numeric.reconcile(broken, PRIMARY))


def test_a_seat_row_that_differs_from_its_record_is_caught(root):
    broken = copy.deepcopy(root)
    broken["panels"]["seats"]["rows"][0]["utilisation_class"] = "active" if root["panels"]["seats"]["rows"][0]["utilisation_class"] != "active" else "unused"
    assert ("T-16", "figure", "seats") in checks(numeric.reconcile(broken, PRIMARY))


# Visual rules catch each kind of break (V-1 to V-8 in M8)


def broken_descriptor(change) -> dict:
    desc = descriptor(2)
    change(desc)
    return desc


def test_a_pie_of_many_slices_and_a_category_comparison_not_as_bars_are_caught(root):
    desc = broken_descriptor(lambda d: panel(d, "recoverable").update(mark="pie"))
    found = checks(visual.check(desc, root))
    assert ("T-17", "pie-slices", "recoverable") in found and ("T-17", "categorical-bar", "recoverable") in found


def test_red_for_a_normal_series_is_caught():
    desc = broken_descriptor(lambda d: panel(d, "trend")["series"][1].update(role="negative"))
    assert ("T-19", "red-for-faults", "trend") in checks(visual.check(desc))


def test_an_off_palette_colour_and_a_class_in_two_colours_are_caught():
    def change(d):
        panel(d, "entitlement")["series"][2]["role"] = "series-3"  # Active, which is positive elsewhere
        panel(d, "recoverable")["series"][0]["role"] = "#d4572a"

    found = checks(visual.check(broken_descriptor(change)))
    assert ("T-19", "class-colour", "entitlement") in found and ("T-19", "palette", "recoverable") in found


def test_mixed_formats_and_a_missing_currency_are_caught():
    def change(d):
        panel(d, "k-entitled")["format"] = "plain"
        column = next(c for c in panel(d, "candidates")["columns"] if c["id"] == "recoverable_year")
        column["format"] = "count"

    found = checks(visual.check(broken_descriptor(change)))
    assert ("T-18", "format", "k-entitled") in found and ("T-18", "currency", "candidates") in found


def test_missing_axis_names_and_units_are_caught():
    def change(d):
        for pid in ("entitlement", "trend"):
            panel(d, pid)["value"]["axis"] = {"name": "", "unit": None}

    found = checks(visual.check(broken_descriptor(change)))
    assert {("T-18", "axis-label", "entitlement"), ("T-18", "axis-unit", "trend")} <= found


def test_cards_off_the_grid_and_uneven_rows_are_caught():
    def change(d):
        panel(d, "k-active")["span"] = 4
        panel(d, "trend")["height"] = 300

    found = checks(visual.check(broken_descriptor(change)))
    assert ("T-19", "grid", "k-recoverable") in found or ("T-19", "grid", "k-idle") in found
    assert any(t == "T-19" and c == "grid" and p == "entitlement" for t, c, p in found)


def test_a_second_title_font_is_caught():
    desc = broken_descriptor(lambda d: panel(d, "trend").update(font={"title": "serif"}))
    assert ("T-19", "font", "trend") in checks(visual.check(desc))


def test_low_contrast_text_is_caught(monkeypatch):
    real = tokens.colour

    def lighter(theme, token, *args):
        return "#c8ccd4" if token == "text-secondary" and theme == "light" else real(theme, token, *args)

    monkeypatch.setattr(tokens, "colour", lighter)
    assert ("T-20", "contrast", "candidates") in checks(visual.check(DESC))


def test_tokens_are_read_from_tokens_css():
    assert tokens.colour("light", "chart-positive") == "#1b7f4b"
    assert tokens.colour("dark", "chart-label-on-fill") == tokens.colour("dark", "text-inverse") == "#0e1116"
    assert round(tokens.contrast("#000000", "#ffffff"), 2) == 21.0


# Structure (T-08)


def test_both_estates_give_valid_payloads_of_one_structure():
    payloads = {name: build(DESC, dataset(name), "") for name in ("primary", "alternate")}
    for name, payload in payloads.items():
        assert structure.problems(DESC, payload, dataset(name)) == []
    assert payloads["primary"] != payloads["alternate"]
    assert structure.shape(payloads["primary"]) == structure.shape(payloads["alternate"])


def test_a_payload_missing_a_panel_or_a_value_is_not_valid(root):
    broken = copy.deepcopy(root)
    del broken["panels"]["trend"]
    broken["panels"]["entitlement"]["series"]["active"].pop()
    broken["panels"]["recoverable"]["withheld"][0] = not broken["panels"]["recoverable"]["withheld"][0]
    found = structure.problems(DESC, broken, PRIMARY)
    assert "trend: no data" in found
    assert "entitlement: series active does not have one value per category" in found
    assert "recoverable: withheld flags do not match the missing values" in found
    assert structure.shape(broken) != structure.shape(root)
