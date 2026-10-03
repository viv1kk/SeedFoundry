"""M9: findings from the validators (FR-T-6, FR-T-7, D-14, D-63, R-2). The sample's iteration 1
build raises exactly the catalogue's fourteen findings, iteration 2 none, and the polished dashboard
gives no problem; each finding comes from its own overlay patch, found by recomputing from the
rows, the descriptor and the applied styles, never from the overlay's list."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from seedfoundry.dashboard import build, descriptor, overlay
from seedfoundry.data import dataset
from seedfoundry.engine.script import BuildContext, script
from seedfoundry.sample import sample_files
from seedfoundry.state import IntakeFile
from seedfoundry.validators import findings, latency, numeric, styles, visual
from seedfoundry.validators.problems import Problem
from test_no_em_dash import em_dashes

CATALOGUE = ["N-1", "N-2", "N-3", "N-4", "N-5", "V-1", "V-2", "V-3", "V-4", "V-5", "V-6", "V-7", "V-8", "L-1"]
PRIMARY = dataset("primary")
VALIDATORS = Path(findings.__file__).resolve().parent


def sample() -> list[IntakeFile]:
    return [IntakeFile(id=f"f-{n}", name=name, category=c, content=text) for n, (name, c, text) in enumerate(sample_files(), 1)]


def events(iteration: int) -> list[dict]:
    return [{**e, "sim_t": b.sim_t} for b in script(BuildContext("b-1", iteration, sample())) for e in b.events]


def raised(evts: list[dict]) -> list[dict]:
    return [e for e in evts if e["type"] == "finding.raised" and not e["data"].get("advisory")]


@pytest.fixture(scope="module")
def first() -> list[dict]:
    return events(1)


@pytest.fixture(scope="module")
def second() -> list[dict]:
    return events(2)


# The D-14 test (the M9 exit criterion)


def test_d14_iteration_1_raises_exactly_the_catalogue_and_iteration_2_none(first, second):
    ids = [e["code"] for e in raised(first)]
    assert sorted(ids, key=CATALOGUE.index) == CATALOGUE and len(ids) == len(set(ids)) == 14
    assert all(e["data"]["catalogued"] for e in raised(first))
    assert raised(second) == []


@pytest.mark.parametrize("path", ["", "microsoft", "microsoft/microsoft-365-e3", "microsoft/microsoft-365-e3/unused", "atlassian/jira-software"])
def test_d14_the_polished_dashboard_gives_zero_problems(path):
    desc = descriptor(2)
    payload = build(desc, PRIMARY, path)
    assert numeric.reconcile(payload, PRIMARY) + visual.check(desc, payload) + latency.check(desc) == []


def test_phase_results_match_build_simulation_section_2(first, second):
    def results(evts):
        return {e["phase"]: e["data"]["result"] for e in evts if e["type"] == "phase.completed"}

    one, two = results(first), results(second)
    assert {p: r for p, r in one.items() if r != "passed"} == {"probe": "findings", "harvest": "findings"}
    assert set(two.values()) == {"passed"}
    lines = {e["phase"]: e["message"] for e in first if e["type"] == "phase.completed"}
    assert lines["probe"] == "Stress & Probe: findings (L-1)"
    assert lines["harvest"] == "Harvest Validation: findings (N-1, N-2, N-3, N-4, N-5, V-1, V-2, V-3, V-4, V-5, V-6, V-7, V-8)"


def test_each_finding_is_raised_in_the_sub_step_that_finds_it(first):
    steps = {e["code"]: (e["phase"], e["step"]) for e in raised(first)}
    assert steps["L-1"] == ("probe", "probe.latency")
    assert {steps[i] for i in ("N-1", "N-2", "N-3", "N-4", "N-5")} == {("harvest", "harvest.numeric")}
    assert steps["V-1"] == ("harvest", "harvest.chart")
    assert {steps[i] for i in ("V-2", "V-3", "V-4", "V-5", "V-6", "V-7")} == {("harvest", "harvest.visual")}
    assert steps["V-8"] == ("harvest", "harvest.contrast")
    # Each finding comes before the result of the test that found it.
    order = [e["code"] for e in first if e["type"] in ("finding.raised", "test.result")]
    for e in raised(first):
        assert order.index(e["code"]) < order.index(e["data"]["test"])


# Removing a patch removes exactly its finding from the build (D-14, R-2)


def without_styles_of(defect: str):
    """The overlay's stylesheet without the rule blocks tagged with this defect."""
    css = (styles.STYLES_DIR / overlay.STYLESHEET).read_text(encoding="utf-8")
    head, body = css.split("*/", 1)
    kept, current = [], None
    for block in re.split(r"\n\n", body.strip()):
        tag = re.match(r"/\* (V-\d+):", block)
        current = tag.group(1) if tag else current
        if current != defect:
            kept.append(block)
    return styles.parse(head + "*/\n" + "\n\n".join(kept))


@pytest.mark.parametrize("patch", overlay.OVERLAY, ids=[p.defect for p in overlay.OVERLAY])
def test_removing_one_overlay_patch_removes_exactly_its_finding_from_the_build(patch, monkeypatch):
    if patch.layer == "styles":
        rules = without_styles_of(patch.defect)
        monkeypatch.setattr(styles, "sheet", lambda name, directory=styles.STYLES_DIR: rules)
    else:
        monkeypatch.setattr(overlay, "OVERLAY", tuple(p for p in overlay.OVERLAY if p is not patch))
    ids = {e["code"] for e in raised(events(1))}
    assert ids == set(CATALOGUE) - {patch.defect}


# What each finding carries (FR-T-7, AC-2)


def test_every_finding_carries_the_fields_of_fr_t_7(first):
    titles = {p["id"]: p["title"] for p in descriptor(1)["panels"]}
    for e in raised(first):
        f = e["data"]
        assert f["id"] == e["code"] and f["category"] in ("Numeric", "Visual", "Latency")
        assert f["severity"] == {"Numeric": "high", "Visual": "medium", "Latency": "medium"}[f["category"]]
        assert e["level"] == {"high": "FAIL", "medium": "WARN"}[f["severity"]]
        assert f["panel"] == f["panels"][0] and f["panel_titles"] == [titles[p] for p in f["panels"]]
        assert f["expected"] and f["shown"] and f["expected"] != f["shown"]
        assert f["phase"] == e["phase"] and f["step"] == e["step"] and f["test"].startswith("T-")
        assert e["message"] == f"{f['id']} {f['message']}" and f["problems"]
    panels = {e["code"]: e["data"]["panels"] for e in raised(first)}
    assert panels["V-3"] == ["seats-treemap", "entitlement"]
    assert panels["V-6"] == ["k-assigned", "k-active", "k-idle", "seats-treemap", "seats"]


def test_expected_and_shown_come_from_the_data(first):
    """AC-2: each N finding's figures are the recount and the payload, from the rows."""
    rows = PRIMARY.seats
    true = build(descriptor(2), PRIMARY, "")["panels"]
    shown = build(descriptor(1), PRIMARY, "")["panels"]
    by = {e["code"]: e["data"] for e in raised(first)}
    entitled = len(rows)
    assert (by["N-1"]["expected"], by["N-1"]["shown"]) == (f"{entitled:,}", f"{sum(shown['entitlement']['series']['entitled']):,}")
    assert by["N-1"]["message"].startswith(f"Entitled seats: KPI shows {entitled:,}, product chart sums to {round(entitled * 1.2):,}")
    assert by["N-2"]["shown"] == f"{sum(i['share'] for i in shown['seats-treemap']['legend']):.1f}%"
    recoverable = sum(12 * s.unit_cost for s in rows if s.utilisation_class in ("unused", "leaver", "unassigned") and s.unit_cost is not None)
    assert by["N-3"]["expected"] == f"${recoverable:,}" == f"${true['k-recoverable']['value']:,}"
    assert by["N-3"]["shown"] == f"${shown['k-recoverable']['value']:,}"
    assert (by["N-4"]["expected"], by["N-4"]["shown"]) == (f"{entitled:,}", f"{sum(1 for s in rows if s.assignee):,}")
    assert by["N-5"]["shown"] == f"{shown['candidates']['total']['entitled']:,}" and by["N-5"]["expected"] == f"{entitled:,}"
    assert (by["L-1"]["expected"], by["L-1"]["shown"]) == ("at most 1.0 s", "4.5 s")
    assert by["L-1"]["message"] == 'Panel "Seats by vendor and product" responds in 4.5 s (budget 1.0 s)'
    assert by["V-1"]["shown"] == f"{sum(1 for v in shown['recoverable']['values'] if v is not None)} slices"
    assert by["V-4"]["shown"] == f"{entitled} (plain)" and by["V-4"]["expected"] == f"{entitled:,} (count)"


def test_no_finding_message_has_an_em_dash(first, second):
    for e in raised(first) + raised(second):
        assert em_dashes(e["message"]) == []
        for p in e["data"]["problems"]:
            assert em_dashes(p["message"]) == []


# The mapping (D-63)


def test_the_mapping_reads_validator_output_never_the_overlay():
    source = (VALIDATORS / "findings.py").read_text(encoding="utf-8")
    assert "overlay" not in re.sub(r'""".*?"""|#.*', "", source, flags=re.S)
    for module in VALIDATORS.glob("*.py"):
        assert "import overlay" not in module.read_text(encoding="utf-8") and "OVERLAY" not in module.read_text(encoding="utf-8"), module.name


def test_several_problems_make_one_finding_in_catalogue_order():
    desc = descriptor(1)
    payload = build(desc, PRIMARY, "")
    problems = latency.check(desc) + numeric.reconcile(payload, PRIMARY) + visual.check(desc, payload)
    found = findings.assign(problems, {p["id"]: p["title"] for p in desc["panels"]})
    assert [f.id for f in found] == CATALOGUE
    assert sum(len(f.problems) for f in found) == len(problems)
    assert len(next(f for f in found if f.id == "N-1").problems) == 18


def test_a_problem_no_catalogue_entry_owns_gets_its_own_id():
    problems = [
        Problem("T-16", "figure", "trend", 5, 6, "Trend: assigned seats by month: shows 6, the recount gives 5"),
        Problem("T-16", "figure", "trend", 7, 8, "Trend: seats in use by month: shows 8, the recount gives 7"),
        Problem("T-16", "part-sum", "entitlement", 10, 12, "Entitled seats: KPI shows 10, product chart sums to 12"),
        Problem("T-16", "kpi-formula", "k-active", 3, 4, "Active KPI: shows 4, the recount gives 3"),
    ]
    found = findings.assign(problems, {"trend": "Assigned and in use, by month", "entitlement": "E", "k-active": "Active"})
    assert [(f.id, f.catalogued, len(f.problems)) for f in found] == [("N-1", True, 1), ("N-X1", False, 2), ("N-X2", False, 1)]
    assert found[1].as_data()["panel_titles"] == ["Assigned and in use, by month"]


def test_the_build_uses_the_same_mapping_with_a_new_problem(monkeypatch):
    """A problem outside the catalogue (a user's own Seed) is raised, never dropped, and the phase reads findings."""
    real = numeric.reconcile

    def extra(payload, data):
        return real(payload, data) + [Problem("T-16", "figure", "trend", 1, 2, "Trend: months: shows 2, the recount gives 1")]

    monkeypatch.setattr(numeric, "reconcile", extra)
    evts = events(2)
    assert [e["code"] for e in raised(evts)] == ["N-X1"]
    harvest = next(e for e in evts if e["type"] == "phase.completed" and e["phase"] == "harvest")
    assert harvest["data"]["result"] == "findings"
    assert evts[-1]["data"]["verdict"]["id"] == "findings"
