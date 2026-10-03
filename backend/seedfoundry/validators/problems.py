"""What a validator reports: the test, the check, the panel, what was expected and what the payload,
descriptor or styles show, and a message that reads on its own. M9 groups problems into findings
(findings.py, FR-T-7) and maps them to the catalogue's ids by test, check and panel; a problem
never names a defect itself."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


def display(value: Any, unit: str = "") -> str:
    """A value as the report shows it: counts with separators, money with $, shares with %."""
    if value is None:
        return "none"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (list, tuple)):
        return ", ".join(display(v, unit) for v in value)
    if isinstance(value, (int, float)):
        if unit == "$":
            return f"${value:,.0f}"
        if unit == "%":
            return f"{value:.1f}%"
        if unit == ":1":
            return f"{value:.2f}:1"
        if unit == "s":
            return f"{value:.1f} s"
        return f"{value:,}" if isinstance(value, int) else f"{value:,.2f}"
    return str(value)


@dataclass(frozen=True)
class Problem:
    test: str  # T-15 to T-20
    check: str  # the rule, e.g. "part-sum", "palette"
    panel: str
    expected: Any
    shown: Any
    message: str
    unit: str = ""  # how expected and shown read: "" counts, "$", "%", ":1", "s"

    @property
    def expected_text(self) -> str:
        return display(self.expected, self.unit)

    @property
    def shown_text(self) -> str:
        return display(self.shown, self.unit)

    def as_data(self) -> dict[str, Any]:
        return asdict(self)
