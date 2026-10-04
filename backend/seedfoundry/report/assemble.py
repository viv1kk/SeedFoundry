"""The build report (FR-R-1, FR-R-2, FR-R-4, ui-spec.md §4, D-64), assembled from a finished build's
kept events (D-49) and nothing else, so it reads the same after a server restart and two runs of
the same build give the same report (NFR-1). Seqs and `wall_ts` are left out; every time is
simulated, from `sim_t`.

- Header: verdict, iteration, Seed name, fingerprint, simulated duration, counts.
- Phases: each phase's result, duration, tests and findings.
- Findings grouped Numeric, Visual, Latency, then Boundary (advisories, which never change the
  verdict, D-12).
- Tests: every test with its phase, name, result and detail.
- Gates: each auto-resolved Seed v0.1 gate, how it was resolved and from which section.
- Simulated usage: LLM calls and tokens, API calls, sandbox time.
- Iteration 2 only, "Changes since iteration 1" (FR-R-3, D-68): every iteration 1 finding, resolved
  when this build raised none with its id; the observer feedback as build 2 kept it; and how the
  routing updated the four files, from this build's Apply observer feedback lines. It reads iteration
  1's kept log too, which never changes once iteration 2 has started, so it is still the same report
  for the same build and after a restart.
"""

from __future__ import annotations

from typing import Any

from seedfoundry.engine.catalogue import PHASES, TEST_NAMES
from seedfoundry.events import Event
from seedfoundry.intake.feedback import feedback_file, segments
from seedfoundry.state import Build
from seedfoundry.validators.findings import order

GROUPS = ("Numeric", "Visual", "Latency", "Boundary")

# The verdict and its tone (D-64): a fault is red; findings are a caution, not a fault.
VERDICTS = {
    "failed": ("Failed", "negative"),
    "incomplete": ("Incomplete", "neutral"),
    "findings": ("Completed with findings", "warning"),
    "passed": ("Passed", "positive"),
}


def verdict(results: dict[str, str], findings: list[dict[str, Any]]) -> dict[str, str]:
    """Failed when a test failed with no finding to show for it; incomplete when a test did not
    run; completed with findings when a finding (not an advisory) was raised; passed otherwise."""
    raised = [f for f in findings if not f.get("advisory")]
    explained = {f.get("test") for f in raised}
    if any(status == "fail" and test not in explained for test, status in results.items()):
        key = "failed"
    elif "not_run" in results.values():
        key = "incomplete"
    elif raised:
        key = "findings"
    else:
        key = "passed"
    label, tone = VERDICTS[key]
    return {"id": key, "label": label, "tone": tone}


def _of(events: list[Event], type_: str) -> list[Event]:
    return [e for e in events if e.type == type_]


def raised(build: Build) -> list[dict[str, Any]]:
    """The build's findings, advisories aside, in catalogue order."""
    found = [e.data for e in _of(build.log, "finding.raised") if not e.data.get("advisory")]
    return sorted(found, key=lambda f: order(f["id"]))


def changes(build: Build, prior: Build | None) -> dict[str, Any]:
    """Changes since iteration 1 (FR-R-3): iteration 1's findings, each resolved when this build has
    none of that id, the feedback that started this build, and the edits its routing made."""
    now = {f["id"] for f in raised(build)}
    findings = [
        {
            "id": f["id"],
            "category": f.get("category"),
            "panel_titles": f.get("panel_titles", []),
            "message": f.get("message", ""),
            "severity": f.get("severity"),
            "status": "open" if f["id"] in now else "resolved",
        }
        for f in (raised(prior) if prior is not None else [])
    ]
    feedback = feedback_file(build.files)
    steps = [e for e in build.log if e.type == "log" and (e.step or "").startswith("assay.feedback-")]
    updates = [
        {k: e.data.get(k) for k in ("file", "section", "segments", "lines_added", "created")}
        for e in steps
        if e.data.get("segments") and e.data.get("lines_added")
    ]
    kept = next((e.data.get("kept", []) for e in steps if "routed" in e.data and "kept" in e.data), [])
    return {
        "prior_build_id": prior.id if prior is not None else None,
        "findings": findings,
        "resolved": sum(1 for f in findings if f["status"] == "resolved"),
        "open": sum(1 for f in findings if f["status"] == "open"),
        "feedback": {"name": feedback.name, "content": feedback.content, "segments": len(segments(feedback.content))} if feedback else None,
        "updates": updates,
        "kept": kept,
    }


def assemble(build: Build, prior: Build | None = None) -> dict[str, Any]:
    """The report of a completed build, from its kept log. For iteration 2, `prior` is iteration 1's
    completed build, which "Changes since iteration 1" reads."""
    events = build.log
    completed = next(e for e in reversed(events) if e.type == "build.completed")
    names = {p.id: p.name for p in PHASES}

    tests = []
    for e in _of(events, "test.result"):
        tests.append(
            {
                "id": e.data["id"],
                "name": e.data.get("name", TEST_NAMES.get(e.data["id"], "")),
                "phase": e.phase,
                "phase_name": names.get(e.phase or "", ""),
                "status": e.data["status"],
                "detail": e.data.get("detail", ""),
                "simulated": bool(e.data.get("simulated")),
            }
        )
    results = {t["id"]: t["status"] for t in tests}

    raised = [{**e.data, "found_at": e.sim_t} for e in _of(events, "finding.raised")]
    findings = [f for f in raised if not f.get("advisory")]
    advisories = [f for f in raised if f.get("advisory")]
    findings.sort(key=lambda f: order(f["id"]))
    groups = [
        {"category": category, "findings": [f for f in (advisories if category == "Boundary" else findings) if f.get("category") == category]}
        for category in GROUPS
    ]

    started = {e.phase: e.sim_t for e in _of(events, "phase.started")}
    phases = []
    for e in _of(events, "phase.completed"):
        phases.append(
            {
                "id": e.phase,
                "index": e.data["index"],
                "name": e.data["name"],
                "result": e.data["result"],
                "duration": round((e.sim_t or 0) - (started.get(e.phase) or 0), 3),
                "tests": e.data.get("tests", {}),
                "findings": [f["id"] for f in findings if f.get("phase") == e.phase],
            }
        )

    gates = [
        {
            "id": e.code,
            "kind": e.data.get("kind"),
            "stage": e.data.get("stage"),
            "resolution": e.data.get("resolution"),
            "basis": e.data.get("basis"),
            "message": e.message,
        }
        for e in _of(events, "gate.auto_resolved")
    ]

    llm = _of(events, "llm.call")
    api = _of(events, "api.call")
    # Sandbox time: from the sandbox's provisioning to its teardown, in simulated seconds.
    provisioned = next((e.sim_t for e in api if e.step == "contain.sandbox"), None)
    torn_down = next((e.sim_t for e in api if e.step == "report.teardown"), None)
    usage = {
        "llm_calls": len(llm),
        "tokens_in": sum(int(e.data.get("tokens_in", 0)) for e in llm),
        "tokens_out": sum(int(e.data.get("tokens_out", 0)) for e in llm),
        "api_calls": len(api),
        "sandbox_seconds": round(torn_down - provisioned, 1) if provisioned is not None and torn_down is not None else 0.0,
        "simulated": True,
    }

    counts = completed.data.get("counts", {})
    return {
        "build_id": build.id,
        "iteration": build.iteration,
        "seed_name": build.seed_name,
        "fingerprint": build.fingerprint,
        "verdict": verdict(results, raised),
        "duration": completed.data.get("sim_seconds", completed.sim_t),
        "counts": {
            "phases": len(phases),
            "phases_with_findings": sum(1 for p in phases if p["result"] == "findings"),
            "tests": len(tests),
            "pass": counts.get("pass", 0),
            "warn": counts.get("warn", 0),
            "fail": counts.get("fail", 0),
            "not_run": counts.get("not_run", 0),
            "findings": len(findings),
            "advisories": len(advisories),
            "gates": len(gates),
        },
        "phases": phases,
        "groups": groups,
        "tests": tests,
        "gates": gates,
        "usage": usage,
        "changes": changes(build, prior) if build.iteration == 2 else None,
    }


def summary(report: dict[str, Any]) -> dict[str, Any]:
    """What report.ready carries: enough for a client to know the verdict without the report."""
    return {
        "verdict": report["verdict"],
        "counts": report["counts"],
        "findings": {g["category"]: [f["id"] for f in g["findings"]] for g in report["groups"]},
    }
