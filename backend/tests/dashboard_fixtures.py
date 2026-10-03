"""Real dashboard responses for the frontend's tests (frontend/tests/fixtures/dashboard/).

The frontend's fake server replays these, so its page tests read what the backend serves. Each
iteration has its own set (iteration-1/ is the rough dashboard with the defect overlay, iteration-2/
the polished one, D-60). `test_dashboard.py` fails when a fixture no longer matches the backend;
rewrite them with

    uv run python tests/dashboard_fixtures.py        (from backend/)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

if __name__ == "__main__":  # run as a script, the backend package is beside tests/, not on the path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from seedfoundry.dashboard import dashboard  # noqa: E402

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "frontend" / "tests" / "fixtures" / "dashboard"

ITERATIONS = (1, 2)

# file: (drill, page, sort, direction), written for each iteration.
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


def path(iteration: int, name: str) -> Path:
    return FIXTURE_DIR / f"iteration-{iteration}" / name


def render(iteration: int, name: str) -> str:
    drill, page, sort, direction = FIXTURES[name]
    return json.dumps(dashboard(iteration, drill=drill or None, page=page, sort=sort, direction=direction), indent=1, ensure_ascii=False) + "\n"


def main() -> None:
    for iteration in ITERATIONS:
        for name in FIXTURES:
            target = path(iteration, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(render(iteration, name), encoding="utf-8", newline="\n")
            print(f"wrote iteration-{iteration}/{name}")


if __name__ == "__main__":
    main()
