"""M9: Stress & Probe's protection and malformed input probes (T-13, T-14, FR-T-5, D-62). Rules come
from the intake's Protection layer and are evaluated as Seed v0.1's policy evaluation does; malformed
inputs go to the record contract and the drill parser. Results are computed, never printed."""

from __future__ import annotations

import pytest

from seedfoundry.data import dataset
from seedfoundry.engine.script import BuildContext, script
from seedfoundry.sample import sample_files
from seedfoundry.state import Category, IntakeFile
from seedfoundry.validators import protection, records
from seedfoundry.validators.protection import ALLOW, DENY, Probe, Rule

PRIMARY = dataset("primary")


def sample() -> list[IntakeFile]:
    return [IntakeFile(id=f"f-{n}", name=name, category=c, content=text) for n, (name, c, text) in enumerate(sample_files(), 1)]


def with_environment(text: str) -> list[IntakeFile]:
    return [f.model_copy(update={"content": text}) if f.category == Category.ENVIRONMENT else f for f in sample()]


def rule(rule_id: str, effect: str, actions: tuple[str, ...], resource: str = "*", **when: str) -> Rule:
    return Rule(rule_id, effect, actions, resource, tuple(when.items()), "environment.md", "Protection Layer", 1, "")


def probe_events(files: list[IntakeFile]) -> list[dict]:
    return [e for b in script(BuildContext("b-1", 1, files)) for e in b.events if e.get("step") in ("probe.protection", "probe.malformed")]


# T-13: the rules (D-62)


def test_rules_come_from_the_samples_protection_layer_with_their_lines():
    files = sample()
    environment = next(f for f in files if f.category == Category.ENVIRONMENT)
    lines = environment.content.split("\n")
    found = protection.rules(files)
    assert [(r.id, r.effect, r.actions, r.resource, dict(r.when)) for r in found] == [
        ("P-1", ALLOW, ("read",), "*", {}),
        ("P-2", DENY, ("remove", "reassign", "change", "delete", "write"), "*", {}),
        ("P-3", DENY, ("remove", "reassign", "change"), "seat", {}),
        ("P-4", ALLOW, ("show_cost",), "product", {"priced": "yes"}),
        ("P-5", DENY, ("show_cost",), "product", {"priced": "no"}),
        ("P-6", ALLOW, ("show_names",), "names", {"level": "seat"}),
        ("P-7", DENY, ("show_names",), "names", {"level": "summary"}),
        ("P-8", DENY, ("export",), "names", {}),
        ("P-9", DENY, ("send",), "dataset", {"destination": "outside"}),
    ]
    for r in found:
        assert r.file == "environment.md" and r.section == "Protection Layer"
        assert r.text in lines[r.line - 1]  # the cited line holds the sentence


def test_no_rule_comes_from_outside_the_protection_layer():
    text = "# Environment\n\n## Data Layer\n\n- Read only files.\n- The dataset stays inside the sandbox.\n"
    assert protection.rules(with_environment(text)) == []


# T-13: Seed v0.1's evaluation (seed-reuse-notes.md §2.6)


def test_the_strictest_effect_wins_and_the_most_specific_rule_is_cited():
    rules = [rule("P-1", ALLOW, ("remove",)), rule("P-2", DENY, ("remove",)), rule("P-3", DENY, ("remove",), "seat")]
    decision = protection.evaluate(rules, Probe("x", "remove a seat", "remove", "seat", (), DENY))
    assert (decision.effect, decision.rule.id) == (DENY, "P-3")


def test_a_missing_fact_is_denied_under_the_default_rule():
    rules = [rule("P-1", ALLOW, ("show_cost",), "product", priced="yes")]
    decision = protection.evaluate(rules, Probe("x", "cost", "show_cost", "product", (), DENY))
    assert decision.effect == DENY and decision.rule is None and "priced" in decision.reason


def test_a_request_no_rule_allows_is_denied_by_default():
    decision = protection.evaluate([], Probe("x", "read", "read", "seat", (), ALLOW))
    assert decision.effect == DENY and decision.rule is None


# T-13: outcomes and status


def test_the_sample_passes_every_probe_by_a_stated_rule():
    ruleset, decisions, status = protection.run(sample())
    assert status == "pass"
    assert [(d.probe.id, d.effect, d.rule.id if d.rule else None) for d in decisions] == [
        ("PB-1", DENY, "P-3"),
        ("PB-2", DENY, "P-3"),
        ("PB-3", DENY, "P-5"),
        ("PB-4", ALLOW, "P-4"),
        ("PB-5", DENY, None),
        ("PB-6", DENY, "P-7"),
        ("PB-7", ALLOW, "P-6"),
        ("PB-8", DENY, "P-8"),
        ("PB-9", DENY, "P-9"),
        ("PB-10", ALLOW, "P-1"),
    ]


def test_a_layer_without_rules_warns_and_lets_nothing_through():
    _, decisions, status = protection.run(with_environment("# Environment\n\n## Styling\n\nPlain.\n"))
    assert status == "warn"
    assert all(d.effect == DENY for d in decisions)  # the default rule denies everything
    assert {d.outcome for d in decisions} == {"default-only", "over-restrictive", "as-expected"}


def test_an_attack_a_rule_allows_fails():
    decisions, status = protection.judge(protection.rules(sample()) + [rule("P-99", ALLOW, ("reassign",), "seat")])
    assert status == "pass"  # DENY still wins over ALLOW
    decisions, status = protection.judge([rule("P-1", ALLOW, ("reassign", "read"), "seat")])
    assert status == "fail"
    assert next(d for d in decisions if d.probe.id == "PB-2").outcome == "let-through"


def test_t13_in_the_build_logs_each_probe_and_its_basis():
    evts = [e for e in probe_events(sample()) if e["step"] == "probe.protection"]
    logs = [e["message"] for e in evts if e["type"] == "log"]
    assert logs[0] == "Protection rules from environment.md, Protection Layer: 9 rules from 4 lines"
    assert logs[1].startswith("PB-1 remove an Unused seat from the License Management System: DENY by P-3 (environment.md, Protection Layer, line ")
    assert logs[5] == "PB-5 show recoverable cost without knowing whether the product is priced: DENY by the default rule (the request does not state priced)"
    result = next(e for e in evts if e["type"] == "test.result")
    assert result["code"] == "T-13" and result["data"]["status"] == "pass"
    assert result["message"] == "T-13 Protection probes: 10 of 10 probes as expected: 6 denied by Protection rules, 3 allowed, 1 denied by the default rule for a missing fact"


def test_a_thin_protection_layer_warns_t13_and_its_phase_still_passes():
    text = "# Environment\n\n## Protection Layer\n\n- Read only.\n"
    files = with_environment(text)
    beats = script(BuildContext("b-1", 2, files))
    evts = [e for b in beats for e in b.events]
    t13 = next(e for e in evts if e["code"] == "T-13")
    assert t13["data"]["status"] == "warn"  # read only gives no cost or names rule: gaps, nothing let through
    probe = next(e for e in evts if e["type"] == "phase.completed" and e["phase"] == "probe")
    assert probe["data"]["result"] == "passed"  # a warn is not a finding (D-62)


# T-14: malformed inputs (D-62)


def test_every_row_of_both_estates_meets_the_record_contract():
    for name in ("primary", "alternate"):
        data = dataset(name)
        assert [s.seat_id for s in data.seats if records.check(s.row(), data)] == []


def test_each_malformed_row_is_refused_for_its_own_reason():
    row = next(s.row() for s in PRIMARY.seats if s.assignee)
    reasons = {}
    for case in records.malformed(row):
        broken = {k: v for k, v in {**row, **case.change}.items() if k != case.drop}
        found = records.check(broken, PRIMARY)
        assert found, case.what
        reasons[case.what] = found[0]
    assert reasons["a class the usage does not give"].endswith("by music.md's rules)")
    assert reasons["no product field"] == "missing product"
    assert reasons["a month of 40 days"] == "usage holds a count that is not 0 to 31 days"


def test_t14_passes_on_the_sample_and_fails_when_the_check_accepts_anything(monkeypatch):
    result = records.run(PRIMARY)
    assert (result.status, result.refused, result.malformed, result.rows_accepted) == ("pass", 16, 16, 13_050)
    evts = [e for e in probe_events(sample()) if e["step"] == "probe.malformed"]
    assert [e["message"] for e in evts if e["type"] in ("log", "test.result")] == [
        "Seat record contract: 13,050 of 13,050 rows of the primary estate accepted",
        "Malformed seat records: 11 of 11 refused",
        "Drill paths: 5 of 5 malformed refused, 3 of 3 well-formed accepted",
        "T-14 Malformed input rejected: 16 of 16 malformed inputs refused; 13,050 seat rows and 3 drill paths accepted",
    ]
    monkeypatch.setattr(records, "check", lambda row, data: [])
    assert records.run(PRIMARY).status == "fail"
    evts = [e for b in script(BuildContext("b-1", 2, sample())) for e in b.events]
    assert next(e for e in evts if e["code"] == "T-14")["data"]["status"] == "fail"
    probe = next(e for e in evts if e["type"] == "phase.completed" and e["phase"] == "probe")
    assert probe["data"]["result"] == "failed" and probe["message"] == "Stress & Probe: failed (T-14)"
    assert evts[-1]["data"]["verdict"] == {"id": "failed", "label": "Failed", "tone": "negative"}


@pytest.mark.parametrize("name", ["primary", "alternate"])
def test_drill_paths_are_built_on_each_estate(name):
    result = records.run(dataset(name))
    assert len(result.paths_accepted) == 3 and len(result.paths_rejected) == 5
