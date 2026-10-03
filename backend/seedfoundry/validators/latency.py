"""Panel latency (T-15, FR-T-5, build-simulation.md §6.4): each panel declares its simulated
latency in the descriptor, and the probe compares the declared value with the 1.0 s budget. The
value is read, not timed, so the result is the same on any machine (NFR-1).

Minimal in M8 (D-60). From M9 it runs in Stress & Probe, and findings.py maps its problems to a
finding (L-1).
"""

from __future__ import annotations

from typing import Any

from seedfoundry.validators.problems import Problem

BUDGET_MS = 1000


def check(descriptor: dict[str, Any], budget_ms: int = BUDGET_MS) -> list[Problem]:
    """A problem for every panel that declares more latency than the budget."""
    return [
        Problem(
            "T-15",
            "latency",
            panel["id"],
            f"at most {budget_ms / 1000:.1f} s",
            f"{panel['latency_ms'] / 1000:.1f} s",
            f'Panel "{panel["title"]}" responds in {panel["latency_ms"] / 1000:.1f} s (budget {budget_ms / 1000:.1f} s)',
            "",
        )
        for panel in descriptor["panels"]
        if panel.get("latency_ms", 0) > budget_ms
    ]
