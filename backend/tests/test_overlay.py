"""Iteration 1's defect overlay (M8, D-13, D-60, seed-reuse-notes.md §5.8): the named list of
patches, each wrong figure derived from the data by its rule at every drill level (R-9), nothing
else changed, and each of the fourteen defects detectable by recomputing from the rows, the
descriptor and the resolved styles, while iteration 2 gives none."""

from __future__ import annotations

import json
import re
from decimal import ROUND_HALF_UP, Decimal

import pytest

from seedfoundry.dashboard import DASHBOARD_ID, build, dashboard, descriptor, overlay
from seedfoundry.data import CLASSES, dataset
from seedfoundry.validators import latency, numeric, structure, styles, visual

PRIMARY = dataset("primary")
ROUGH = descriptor(1)
POLISHED = descriptor(2)
CATALOGUE = ["N-1", "N-2", "N-3", "N-4", "N-5", "V-1", "V-2", "V-3", "V-4", "V-5", "V-6", "V-7", "V-8", "L-1"]

# A sample of drill levels: the root, a vendor, a priced and an unpriced product, every class of
# a priced product, an unpriced product's Unassigned seats, and a leaf drilled as one step.
LEVELS = [
    "",
    "microsoft",
    "microsoft/microsoft-365-e3",
    "atlassian/jira-software",
    *[f"microsoft/microsoft-365-e3/{c}" for c in CLASSES],
    "atlassian/jira-software/unassigned",
    "salesforce.sales-cloud-enterprise.leaver",
]


def half_up(value, factor: str, places: str = "1"):
    scaled = (Decimal(str(value)) * Decimal(factor)).quantize(Decimal(places), rounding=ROUND_HALF_UP)
    return int(scaled) if places == "1" else float(scaled)


def rows(path: str):
    data = build(POLISHED, PRIMARY, path)["drill"]["filter"]
    return [
        s
        for s in PRIMARY.seats
        if all(data[k] is None or v == data[k] for k, v in (("vendor", s.vendor_id), ("product", s.product_id), ("class", s.utilisation_class)))
    ]


def defect_of(problem) -> str:
    """Which catalogue defect a validator problem points at, by test, check and panel. M9's
    findings will make this mapping; here it shows each defect is detectable on its own."""
    if problem.test == "T-16":
        return {"entitlement": "N-1", "seats-treemap": "N-2", "k-recoverable": "N-3", "seats": "N-4", "candidates": "N-5"}[problem.panel]
    if problem.test == "T-17":
        return "V-1"
    if problem.test == "T-18":
        return "V-5" if problem.check.startswith("axis") else "V-4"
    if problem.test == "T-19":
        return {"red-for-faults": "V-2", "palette": "V-3", "class-colour": "V-3", "font": "V-7"}.get(problem.check, "V-6")
    if problem.test == "T-20":
        return "V-8"
    assert problem.test == "T-15", problem
    return "L-1"


def problems(desc, payload):
    return numeric.reconcile(payload, PRIMARY) + visual.check(desc, payload) + latency.check(desc)


# The overlay as data (D-60)


def test_the_overlay_is_one_named_patch_per_catalogue_defect():
    assert [p.defect for p in overlay.OVERLAY] == CATALOGUE
    for patch in overlay.OVERLAY:
        assert patch.shows and patch.rule and patch.deep and patch.panels
        assert {p for p in patch.panels} <= {p["id"] for p in POLISHED["panels"]}, patch.defect
        if patch.layer == "payload":
            assert patch.payload and not patch.descriptor and patch.defect.startswith("N-")
        elif patch.layer == "descriptor":
            assert patch.descriptor and not patch.payload
        else:
            assert patch.layer == "styles" and not patch.payload and not patch.descriptor


def test_every_styles_patch_has_its_rules_in_defects_css_and_every_rule_names_a_defect():
    css = (styles.STYLES_DIR / overlay.STYLESHEET).read_text(encoding="utf-8")
    style_defects = {p.defect for p in overlay.OVERLAY if p.layer == "styles"}
    named = set(re.findall(r"/\* (V-\d+):", css))
    assert named == style_defects == {"V-6", "V-7", "V-8"}
    # Every rule block follows a comment naming one of them.
    blocks = re.split(r"\n\n", css.split("*/", 1)[1].strip())
    current = None
    for block in blocks:
        tag = re.match(r"/\* (V-\d+):", block)
        current = tag.group(1) if tag else current
        assert current in style_defects, block


def test_the_overlay_endpoint_serves_the_list(client):
    body = client.get(f"/api/dashboards/{DASHBOARD_ID}/overlay").json()
    assert body["applies_to_iteration"] == 1 and body["root_class"] == "defects-overlay"
    assert [p["defect"] for p in body["patches"]] == CATALOGUE
    assert body["patches"][0] == overlay.OVERLAY[0].as_data()


def test_the_dashboard_endpoint_serves_the_rough_variant_for_iteration_1(client):
    body = client.get(f"/api/dashboards/{DASHBOARD_ID}", params={"iteration": 1}).json()
    assert (body["iteration"], body["variant"]) == (1, "rough")
    assert body["descriptor"] == ROUGH
    assert body["payload"] == build(ROUGH, PRIMARY, "")


def test_v3s_colour_is_the_only_raw_colour_and_only_in_iteration_1():
    assert re.findall(r"#[0-9a-fA-F]{3,8}\b", json.dumps(ROUGH)) == [overlay.OFF_PALETTE]
    treemap = next(p for p in ROUGH["panels"] if p["id"] == "seats-treemap")
    assert treemap["class_colours"] == {"unused": {"colour": overlay.OFF_PALETTE}}
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", json.dumps(POLISHED))
    assert "#" not in (styles.STYLES_DIR / overlay.STYLESHEET).read_text(encoding="utf-8")


# Each figure derived from the data by its rule, at every sampled level (R-9)


@pytest.mark.parametrize("path", LEVELS)
def test_each_wrong_figure_is_derived_from_the_data_by_its_rule(path):
    true = build(POLISHED, PRIMARY, path)["panels"]
    shown = build(ROUGH, PRIMARY, path)["panels"]
    seats = rows(path)

    # N-1: each Entitled bar at 1.2 x true, and the keyboard read-out says the same.
    expected = [half_up(v, "1.2") for v in true["entitlement"]["series"]["entitled"]]
    assert shown["entitlement"]["series"]["entitled"] == expected
    by_id = dict(zip((c["id"] for c in shown["entitlement"]["categories"]), expected, strict=True))
    assert all(t["value"] == by_id[t["step"][-1]] for t in shown["entitlement"]["targets"])
    # N-2: each legend share at 1.12 x true.
    assert [i["share"] for i in shown["seats-treemap"]["legend"]] == [half_up(i["share"], "1.12", "0.1") for i in true["seats-treemap"]["legend"]]
    # N-3: the KPI over priced Unused and Underused seats.
    assert shown["k-recoverable"]["value"] == sum(12 * s.unit_cost for s in seats if s.utilisation_class in ("unused", "underused") and s.unit_cost is not None)
    # N-4: the footer total is the assigned count.
    assert shown["seats"]["footer"]["total"] == sum(1 for s in seats if s.assignee is not None)
    # N-5: the total row is the row sums plus the largest row again.
    table = true["candidates"]
    largest = max(table["rows"], key=lambda r: r["entitled"])
    for key in ("entitled", *CLASSES, "recoverable_seats"):
        assert shown["candidates"]["total"][key] == sum(r[key] for r in table["rows"]) + largest[key], key
    assert shown["candidates"]["total"]["recoverable_year"] == sum(r["recoverable_year"] or 0 for r in table["rows"]) + (largest["recoverable_year"] or 0)

    # Nothing else in the payload differs from the polished one.
    def strip(panels):
        out = json.loads(json.dumps(panels))
        out["entitlement"]["series"]["entitled"] = out["entitlement"]["targets"] = None
        for item in out["seats-treemap"]["legend"]:
            item["share"] = None
        out["k-recoverable"]["value"] = out["seats"]["footer"]["total"] = out["candidates"]["total"] = None
        return out

    assert strip(shown) == strip(true)


def test_the_root_figures_read_as_the_catalogue_says():
    shown = build(ROUGH, PRIMARY, "")["panels"]
    kpi = shown["k-entitled"]["value"]
    assert sum(shown["entitlement"]["series"]["entitled"]) == round(kpi * 1.2)  # 13,050 shown, bars sum to 15,660
    assert round(sum(i["share"] for i in shown["seats-treemap"]["legend"]), 1) == 112.0
    assert shown["k-recoverable"]["value"] != sum(v for v in shown["recoverable"]["values"] if v is not None)
    assert shown["seats"]["footer"]["total"] == shown["k-assigned"]["value"] != kpi
    assert shown["candidates"]["total"]["entitled"] > kpi
    assert sum(1 for v in shown["recoverable"]["values"] if v is not None) > 8  # V-1's pie: one slice per priced product


def test_the_overlay_has_no_randomness():
    assert json.dumps(dashboard(1, drill="microsoft/microsoft-365-e3"), sort_keys=True) == json.dumps(dashboard(1, drill="microsoft/microsoft-365-e3"), sort_keys=True)
    assert overlay.apply_descriptor(POLISHED) == overlay.apply_descriptor(POLISHED)


# Each defect detectable from the data, the descriptor and the styles; iteration 2 clean


def test_all_fourteen_defects_are_detected_on_iteration_1_and_nothing_else():
    payload = build(ROUGH, PRIMARY, "")
    found = problems(ROUGH, payload)
    assert sorted({defect_of(p) for p in found}, key=CATALOGUE.index) == CATALOGUE


@pytest.mark.parametrize("path", ["", "microsoft", "microsoft/microsoft-365-e3/unused", "atlassian/jira-software"])
def test_iteration_2_gives_no_problem(path):
    assert problems(POLISHED, build(POLISHED, PRIMARY, path)) == []
    assert styles.applied(POLISHED) == []


def expected_at(path: str) -> list[str]:
    """The catalogue at a level, less the documented exceptions (D-60, seed-reuse-notes.md §5.8)."""
    ids = path.replace(".", "/").split("/") if path else []
    product = PRIMARY.product(ids[1]) if len(ids) > 1 else None
    cls = ids[2] if len(ids) > 2 else None
    gone = set()
    if (product is not None and product.unit_cost is None) or cls in ("active", "unused"):
        gone.add("N-3")  # both sums equal
    if cls is not None and cls != "unassigned":
        gone.add("N-4")  # every seat in the filter is assigned
    return [d for d in CATALOGUE if d not in gone]


@pytest.mark.parametrize("path", LEVELS)
def test_the_overlay_stays_applied_at_drill_levels_with_the_documented_exceptions(path):
    found = {defect_of(p) for p in problems(ROUGH, build(ROUGH, PRIMARY, path))}
    assert sorted(found, key=CATALOGUE.index) == expected_at(path)


def test_each_detection_comes_from_its_own_patch():
    """Remove one patch at a time: its defect is no longer found, every other one still is."""
    for patch in overlay.OVERLAY:
        if patch.layer == "styles":
            continue  # the sheet is one file; its rules are checked by the reader tests below
        rest = tuple(p for p in overlay.OVERLAY if p is not patch)
        original = overlay.OVERLAY
        try:
            overlay.OVERLAY = rest
            desc = overlay.apply_descriptor(POLISHED)
            found = {defect_of(p) for p in problems(desc, build(desc, PRIMARY, ""))}
        finally:
            overlay.OVERLAY = original
        assert patch.defect not in found
        assert found == set(CATALOGUE) - {patch.defect}


def test_the_styles_reader_sees_the_sheets_rules_by_panel():
    rules = styles.applied(ROUGH)
    assert rules and all(r.selector.startswith(".defects-overlay ") for r in rules)
    by_panel = {r.panel for r in rules}
    assert {"k-assigned", "k-active", "k-idle", "seats-treemap", "seats", "trend", "candidates"} <= by_panel
    caption = next(r for r in rules if r.panel == "candidates" and "table-caption" in r.target)
    assert caption.value("color") == "var(--border-default)"  # !important dropped
    found = {(p.test, p.check, p.panel) for p in visual.check(ROUGH, build(ROUGH, PRIMARY, ""))}
    assert {("T-19", "grid", "k-idle"), ("T-19", "overflow", "seats-treemap"), ("T-19", "truncation", "seats"), ("T-19", "font", "trend")} <= found
    assert {("T-20", "contrast", "candidates")} <= found


def test_the_styles_reader_parses_selectors_and_declarations():
    rules = styles.parse("/* x */ .r [data-panel='a'] h3, .r [data-panel=\"b\"] { color: var(--t) !important; width: 10px }")
    assert [(r.panel, r.target) for r in rules] == [("a", "h3"), ("b", "")]
    assert rules[0].declarations == (("color", "var(--t)"), ("width", "10px"))


# T-08 on iteration 1 (D-58): the pie keeps the bar's data shape


def test_the_rough_payload_is_structurally_valid_and_one_shape_on_both_estates():
    payloads = {name: build(ROUGH, dataset(name), "") for name in ("primary", "alternate")}
    for name, payload in payloads.items():
        assert structure.problems(ROUGH, payload, dataset(name)) == [], name
    assert structure.shape(payloads["primary"]) == structure.shape(payloads["alternate"])
    assert structure.shape(payloads["primary"]) == structure.shape(build(POLISHED, PRIMARY, ""))
