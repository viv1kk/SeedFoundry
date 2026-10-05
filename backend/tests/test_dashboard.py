"""The License Optimization dashboard (FR-D-1 to FR-D-6, D-56): the descriptor, the query engine
against row-level ground truth at every level of the hierarchy, the drill path, the Seats table,
determinism, the API, and the frontend's fixtures."""

from __future__ import annotations

import copy
import hashlib
import json
import re

import pytest

from dashboard_fixtures import FIXTURES, ITERATIONS, path, render
from seedfoundry.dashboard import DASHBOARD_ID, QueryError, build, dashboard, descriptor, overlay, parse
from seedfoundry.data import CLASSES, dataset

PRIMARY = dataset("primary")
DESC = descriptor(2)


def every_drill_path(data) -> list[str]:
    """Every level of the hierarchy: all products, each vendor, each product, each class of each product."""
    paths = [""]
    for vendor_id, _ in data.vendors:
        paths.append(vendor_id)
        for product in (p for p in data.products if p.vendor_id == vendor_id):
            paths.append(f"{vendor_id}/{product.id}")
            paths += [f"{vendor_id}/{product.id}/{c}" for c in CLASSES]
    return paths


def truth(data, vendor=None, product=None, cls=None) -> dict:
    """Row-level ground truth, by brute force over the seats."""
    rows = [
        s
        for s in data.seats
        if (vendor is None or s.vendor_id == vendor) and (product is None or s.product_id == product) and (cls is None or s.utilisation_class == cls)
    ]
    recoverable = [s for s in rows if s.utilisation_class in ("unused", "leaver", "unassigned")]
    return {
        "rows": rows,
        "entitled": len(rows),
        "assigned": len([s for s in rows if s.assignee is not None]),
        "active": len([s for s in rows if s.utilisation_class == "active"]),
        "idle": len([s for s in rows if s.utilisation_class in ("unused", "underused")]),
        "recoverable_year": sum(12 * s.unit_cost for s in recoverable if s.unit_cost is not None),
        "withheld": len([s for s in recoverable if s.unit_cost is None]),
        "classes": {c: len([s for s in rows if s.utilisation_class == c]) for c in CLASSES},
    }


# The descriptor (seed-reuse-notes.md §5.3, §5.4, D-27)


def test_the_descriptor_has_the_eleven_panels_in_the_four_bands():
    assert DESC["title"] == "License Optimization"
    assert [b["id"] for b in DESC["bands"]] == ["kpis", "charts", "focus", "records"]
    assert [(p["id"], p["band"], p["mark"]) for p in DESC["panels"]] == [
        ("k-entitled", "kpis", "kpi"),
        ("k-assigned", "kpis", "kpi"),
        ("k-active", "kpis", "kpi"),
        ("k-idle", "kpis", "kpi"),
        ("k-recoverable", "kpis", "kpi"),
        ("seats-treemap", "charts", "treemap"),
        ("entitlement", "charts", "bar"),
        ("trend", "charts", "line"),
        ("recoverable", "charts", "bar"),
        ("candidates", "focus", "table"),
        ("seats", "records", "table"),
    ]
    titles = {p["id"]: p["title"] for p in DESC["panels"]}
    assert titles["seats-treemap"] == "Seats by vendor and product"
    assert titles["trend"] == "Assigned and in use, by month"
    assert titles["seats"] == "Seats"


def test_the_descriptor_binds_colours_to_roles_never_to_hex():
    text = json.dumps(DESC)
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", text)
    assert {c["id"]: c["role"] for c in DESC["classes"]} == {
        "active": "positive",
        "underused": "warning",
        "unused": "anomaly",
        "leaver": "negative",
        "unassigned": "muted",
    }
    roles = {p["id"]: [s["role"] for s in p.get("series", [])] for p in DESC["panels"]}
    assert roles["entitlement"] == ["baseline", "series-1", "positive"]
    # ValueWise house style (D-99): In use is a count, not a status; cost is the Value lens, in
    # gold; the primary KPI is Recoverable a year, with no coloured rule.
    assert roles["trend"] == ["series-1", "series-2"]
    assert roles["recoverable"] == ["value"]
    assert [p["id"] for p in DESC["panels"] if p.get("emphasis") == "primary"] == ["k-recoverable"]
    assert not any("rule_role" in p for p in DESC["panels"])


# Iteration 2 is M7's dashboard; iteration 1 is it plus the overlay (D-13, D-60, D-61)

M7_DIGESTS = {
    # The polished descriptor and payloads as M7 served them (sha256 of the sorted JSON).
    "descriptor": "abcc42a0f17c00a9db153fcad385e8c4bf4bd0509feafc706e6c648a1776598e",
    ("", 1, None, None): "ddb03d6f1d01eaaddbf652a31738bc8ed31be4e929028cd33d70445f142ffe2d",
    ("", 2, None, None): "989ab35699ace315390e8c5826cbc4c2eb3f7f92a80c761f88c0fcf924bb7b98",
    ("", 1, "days_idle", "desc"): "10f61990cfd34c7d4306e0a06ba72686ab68ed4233529ed46e8b5948b801392e",
    ("microsoft", 1, None, None): "31dcc190db9518803a232313991056709b481e6df52404690706f53e4f4d4c86",
    ("microsoft/microsoft-365-e3", 1, None, None): "fcf5c8a6bb77bbf879704e081d3c1ac8307eea3daf051356ec2d158148ca125b",
    ("microsoft.microsoft-365-e3.unused", 1, None, None): "fcfe8d6fa40eb3c4722286f92f2eb0c2971701b9122b4a1e6a99d4517ac5e895",
}


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def as_m7(desc: dict) -> dict:
    """The descriptor with CR-3's house-style changes undone (D-99, D-101): figures and ids back in
    mono, Entitled the primary KPI with its anomaly rule, In use positive, recoverable cost anomaly.
    These are the only differences from M7's descriptor; no figure, format, layout or panel changed."""
    d = copy.deepcopy(desc)
    d["fonts"] = {**d["fonts"], "figure": "mono", "id": "mono"}
    panels = {p["id"]: p for p in d["panels"]}
    panels["k-entitled"].update(emphasis="primary", rule_role="anomaly")
    del panels["k-recoverable"]["emphasis"]
    next(s for s in panels["trend"]["series"] if s["id"] == "in_use")["role"] = "positive"
    panels["recoverable"]["series"][0]["role"] = "anomaly"
    return d


def test_iteration_2_is_the_m7_dashboard_in_the_house_style():
    # D-102: M7's digests are kept; the dashboard is compared with CR-3's style changes undone.
    assert digest(as_m7(descriptor(2))) == M7_DIGESTS["descriptor"]
    assert descriptor(2)["variant"] == "polished" and "styles" not in descriptor(2)
    for (path, page, sort, direction), expected in ((k, v) for k, v in M7_DIGESTS.items() if k != "descriptor"):
        served = dashboard(2, drill=path or None, page=page, sort=sort, direction=direction)
        assert digest({**served, "descriptor": as_m7(served["descriptor"])}) == expected, path


def test_iteration_1_is_the_polished_descriptor_plus_the_overlay():
    rough, polished = descriptor(1), descriptor(2)
    assert rough["variant"] == "rough"
    assert rough["styles"] == {"root_class": "defects-overlay", "sheet": "defects.css"}
    assert overlay.apply_descriptor(polished) == rough
    assert descriptor(2) == polished  # applying the overlay changed nothing in the polished copy
    # Same panels, bands, classes, measures and grid: only the patched fields differ.
    assert [p["id"] for p in rough["panels"]] == [p["id"] for p in polished["panels"]]
    for key in ("bands", "classes", "measures", "grid", "fonts", "surface", "title"):
        assert rough[key] == polished[key], key
    changed = {p["id"] for p, q in zip(rough["panels"], polished["panels"], strict=True) if p != q}
    assert changed == {"k-entitled", "k-active", "seats-treemap", "entitlement", "trend", "recoverable", "candidates"}


# The query engine against ground truth, at every level (D-29 exit criterion)


@pytest.mark.parametrize("path", every_drill_path(PRIMARY))
def test_the_query_engine_matches_row_level_ground_truth(path):
    payload = build(DESC, PRIMARY, path)
    ids = path.split("/") if path else []
    expected = truth(PRIMARY, *(ids + [None] * (3 - len(ids))))
    panels = payload["panels"]
    assert panels["k-entitled"]["value"] == expected["entitled"]
    assert panels["k-assigned"]["value"] == expected["assigned"]
    assert panels["k-active"]["value"] == expected["active"]
    assert panels["k-idle"]["value"] == expected["idle"]
    assert panels["k-recoverable"]["value"] == expected["recoverable_year"]
    assert panels["k-recoverable"]["withheld_seats"] == expected["withheld"]
    assert {i["class"]: i["count"] for i in panels["seats-treemap"]["legend"]} == expected["classes"]
    assert sum(n["value"] for n in panels["seats-treemap"]["nodes"]) == expected["entitled"]
    assert {k: v for k, v in panels["seats"]["footer"].items() if k != "total"} == expected["classes"]
    assert panels["seats"]["footer"]["total"] == panels["seats"]["total"] == expected["entitled"]
    assert sum(panels["entitlement"]["series"]["entitled"]) == expected["entitled"]
    by_product = {r["product_id"]: r for r in panels["candidates"]["rows"]}
    for product_id, row in by_product.items():
        product_truth = truth(PRIMARY, None, product_id, ids[2] if len(ids) == 3 else None)
        assert row["entitled"] == product_truth["entitled"]
        assert {c: row[c] for c in CLASSES} == product_truth["classes"]
    assert panels["candidates"]["total"]["entitled"] == expected["entitled"]
    shown = {r["seat_id"] for r in panels["seats"]["rows"]}
    assert shown <= {s.seat_id for s in expected["rows"]}
    assert len(shown) == min(25, expected["entitled"])


def test_a_class_drill_on_a_product_shows_that_products_seats_only():
    payload = build(DESC, PRIMARY, "microsoft.microsoft-365-e3.unused")
    rows = payload["panels"]["seats"]["rows"]
    assert rows and all(r["product"] == "Microsoft 365 E3" and r["utilisation_class"] == "unused" for r in rows)
    assert payload["drill"]["deepest"] is True and payload["drill"]["level"] == "class"
    leaf = payload["panels"]["seats-treemap"]
    assert [n["id"] for n in leaf["nodes"]] == ["unused"] and leaf["targets"] == []


# The drill path (FR-D-6)


def test_a_leaf_drills_three_levels_in_one_step_and_its_crumb_names_each():
    drill = parse(PRIMARY, "microsoft.microsoft-365-e3.unused")
    assert len(drill.steps) == 1 and drill.depth == 3
    assert [c["label"] for c in drill.crumbs()] == ["All products", "Microsoft › Microsoft 365 E3 › Unused"]
    assert [c["path"] for c in drill.crumbs()] == ["", "microsoft.microsoft-365-e3.unused"]


def test_steps_drilled_one_at_a_time_each_have_a_crumb():
    drill = parse(PRIMARY, "microsoft/microsoft-365-e3/unused")
    assert [c["label"] for c in drill.crumbs()] == ["All products", "Microsoft", "Microsoft 365 E3", "Unused"]
    assert [c["path"] for c in drill.crumbs()] == ["", "microsoft", "microsoft/microsoft-365-e3", "microsoft/microsoft-365-e3/unused"]


def test_one_step_and_three_steps_select_the_same_seats():
    one = build(DESC, PRIMARY, "microsoft.microsoft-365-e3.unused")["panels"]
    three = build(DESC, PRIMARY, "microsoft/microsoft-365-e3/unused")["panels"]
    assert one == three


def test_drill_targets_append_the_next_levels():
    root = build(DESC, PRIMARY, "")["panels"]
    vendor = root["seats-treemap"]["nodes"][0]
    product = vendor["children"][0]
    leaf = product["children"][0]
    assert vendor["step"] == [vendor["id"]]
    assert product["step"] == [vendor["id"], product["id"]]
    assert leaf["step"] == [vendor["id"], product["id"], leaf["id"]]
    bar = root["entitlement"]["categories"][0]
    assert bar["step"] == [PRIMARY.product(bar["id"]).vendor_id, bar["id"]]
    under_vendor = build(DESC, PRIMARY, "microsoft")["panels"]
    assert all(len(c["step"]) == 1 for c in under_vendor["entitlement"]["categories"])
    assert all(n["step"] == [n["id"]] for n in under_vendor["seats-treemap"]["nodes"])
    under_product = build(DESC, PRIMARY, "microsoft/microsoft-365-e3")["panels"]
    assert all(c["step"] is None for c in under_product["entitlement"]["categories"])
    assert under_product["entitlement"]["targets"] == []
    assert [n["step"] for n in under_product["seats-treemap"]["nodes"]] == [[c] for c in CLASSES]


@pytest.mark.parametrize(
    "path",
    ["adobe/microsoft-365-e3", "nobody", "microsoft/nothing", "microsoft/microsoft-365-e3/idle", "microsoft//x", "a.b.c.d", "microsoft/microsoft-365-e3/unused/x"],
)
def test_a_path_the_data_does_not_have_is_refused(path):
    with pytest.raises(QueryError) as refused:
        parse(PRIMARY, path)
    assert refused.value.status == 404 and refused.value.code == "drill_not_found"


# The Seats table


def test_seats_are_paginated_and_sortable():
    first = build(DESC, PRIMARY, "", 1)["panels"]["seats"]
    second = build(DESC, PRIMARY, "", 2)["panels"]["seats"]
    assert first["pages"] == -(-len(PRIMARY.seats) // 25) and first["page_size"] == 25
    assert (first["first"], first["last"], second["first"], second["last"]) == (1, 25, 26, 50)
    assert [r["seat_id"] for r in first["rows"] + second["rows"]] == sorted(s.seat_id for s in PRIMARY.seats)[:50]
    last = build(DESC, PRIMARY, "", 10_000)["panels"]["seats"]
    assert last["page"] == last["pages"] and last["rows"]
    idle = build(DESC, PRIMARY, "", 1, "days_idle", "desc")["panels"]["seats"]["rows"]
    days = [r["days_idle"] for r in idle]
    assert days == sorted(days, reverse=True)
    never = build(DESC, PRIMARY, "", last["pages"], "days_idle", "desc")["panels"]["seats"]["rows"]
    assert never[-1]["days_idle"] is None  # empty values sort last
    classes = build(DESC, PRIMARY, "microsoft", 1, "utilisation_class", "asc")["panels"]["seats"]["rows"]
    assert [r["utilisation_class"] for r in classes] == ["active"] * 25


@pytest.mark.parametrize(("sort", "direction"), [("assignee_status", "asc"), ("usage", "asc"), ("seat_id", "up")])
def test_an_unknown_sort_is_refused(sort, direction):
    with pytest.raises(QueryError) as refused:
        build(DESC, PRIMARY, "", 1, sort, direction)
    assert refused.value.status == 400


# Determinism (NFR-1)


def test_the_same_request_gives_the_same_payload():
    assert json.dumps(dashboard(1, drill="microsoft"), sort_keys=True) == json.dumps(dashboard(1, drill="microsoft"), sort_keys=True)


def test_the_payload_carries_no_wall_clock():
    text = json.dumps(dashboard(1))
    assert not re.search(r"20\d\d-\d\d-\d\dT\d\d:", text)
    assert "wall_ts" not in text


# The API


def test_the_dashboard_endpoint_serves_descriptor_and_payload(client):
    response = client.get(f"/api/dashboards/{DASHBOARD_ID}", params={"iteration": 2, "drill": "microsoft.microsoft-365-e3.unused"})
    assert response.status_code == 200
    body = response.json()
    assert (body["id"], body["iteration"], body["variant"]) == (DASHBOARD_ID, 2, "polished")
    assert body["descriptor"] == descriptor(2)
    assert body["payload"]["drill"]["crumbs"][-1]["label"] == "Microsoft › Microsoft 365 E3 › Unused"


def test_the_dashboard_endpoint_refuses_what_does_not_exist(client):
    missing = client.get(f"/api/dashboards/{DASHBOARD_ID}", params={"iteration": 1, "drill": "nobody"})
    assert missing.status_code == 404 and missing.json()["detail"]["code"] == "drill_not_found"
    assert client.get("/api/dashboards/spend", params={"iteration": 1}).json()["detail"]["code"] == "dashboard_not_found"
    # D-81: iterations go on past 2, and every one after the first shows the polished dashboard.
    assert client.get(f"/api/dashboards/{DASHBOARD_ID}", params={"iteration": 0}).status_code == 422
    later, second = (client.get(f"/api/dashboards/{DASHBOARD_ID}", params={"iteration": n}).json() for n in (3, 2))
    assert later.pop("iteration") == 3 and second.pop("iteration") == 2 and later == second
    assert client.get(f"/api/dashboards/{DASHBOARD_ID}", params={"iteration": 1, "dataset": "x"}).status_code == 404
    assert client.get(f"/api/dashboards/{DASHBOARD_ID}", params={"iteration": 1, "sort": "usage"}).status_code == 400


def test_descriptor_payload_and_data_are_each_inspectable(client):
    assert client.get(f"/api/dashboards/{DASHBOARD_ID}/descriptor", params={"iteration": 2}).json() == descriptor(2)
    alternate = client.get(f"/api/dashboards/{DASHBOARD_ID}", params={"iteration": 2, "dataset": "alternate"}).json()
    assert alternate["payload"]["dataset"]["name"] == "alternate"
    listed = client.get("/api/datasets").json()
    assert [d["name"] for d in listed] == ["primary", "alternate"]
    rows = client.get("/api/datasets/primary").json()
    assert len(rows["seat_rows"]) == rows["seats"] == len(PRIMARY.seats)
    assert rows["seat_rows"][0]["usage"] == list(PRIMARY.seats[0].usage)
    assert client.get("/api/datasets/other").status_code == 404


# The frontend's fixtures


@pytest.mark.parametrize("iteration", ITERATIONS)
@pytest.mark.parametrize("name", FIXTURES)
def test_the_frontend_fixtures_are_what_the_backend_serves(iteration, name):
    fixture = path(iteration, name)
    assert fixture.exists(), f"run: uv run python tests/dashboard_fixtures.py (iteration-{iteration}/{name} is missing)"
    assert fixture.read_text(encoding="utf-8") == render(iteration, name), f"iteration-{iteration}/{name} is stale: run uv run python tests/dashboard_fixtures.py"
