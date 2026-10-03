"""Real dashboard responses for the frontend's tests (frontend/tests/fixtures/dashboard/).

The frontend's fake server replays these, so its page tests read what the backend serves.
`test_dashboard.py` fails when a fixture no longer matches the backend; rewrite them with

    uv run python tests/dashboard_fixtures.py        (from backend/)
"""

from __future__ import annotations

import json
from pathlib import Path

from seedfoundry.dashboard import dashboard

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "frontend" / "tests" / "fixtures" / "dashboard"

# file: (drill, page, sort, direction). Iteration 1; the fake server sets the iteration it is asked for.
FIXTURES = {
    "root.json": ("", 1, None, None),
    "root-page-2.json": ("", 2, None, None),
    "root-days-idle-asc.json": ("", 1, "days_idle", "asc"),
    "root-days-idle-desc.json": ("", 1, "days_idle", "desc"),
    "vendor.json": ("microsoft", 1, None, None),
    "vendor-product.json": ("microsoft/microsoft-365-e3", 1, None, None),
    "product-step.json": ("microsoft.microsoft-365-e3", 1, None, None),
    "leaf.json": ("microsoft.microsoft-365-e3.unused", 1, None, None),
    "leaf-steps.json": ("microsoft/microsoft-365-e3/unused", 1, None, None),
}


def render(name: str) -> str:
    drill, page, sort, direction = FIXTURES[name]
    return json.dumps(dashboard(1, drill=drill or None, page=page, sort=sort, direction=direction), indent=1, ensure_ascii=False) + "\n"


def main() -> None:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    for name in FIXTURES:
        (FIXTURE_DIR / name).write_text(render(name), encoding="utf-8", newline="\n")
        print(f"wrote {name}")


if __name__ == "__main__":
    main()
