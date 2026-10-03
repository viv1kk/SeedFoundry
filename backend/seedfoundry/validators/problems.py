"""What a validator reports. M9 turns problems into findings (FR-T-7) and maps them to the
catalogue's ids; until then a problem is the check, the panel, what was expected and what the
payload or descriptor shows."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Problem:
    test: str  # T-16 to T-20
    check: str  # the rule, e.g. "part-sum", "palette"
    panel: str
    expected: Any
    shown: Any
    message: str

    def as_data(self) -> dict[str, Any]:
        return asdict(self)
