"""Golden Seed files for both approval paths, and the Seed page's data for the frontend's tests.

The sample's two builds are report_fixtures.py's (the real engine on a fake clock: iteration 1, then
the rebuild with the demo feedback). Approving iteration 2 gives files with learned rules and no
known issues; approving iteration 1 (before any rebuild) gives files with every open finding as a
known issue and no learned rules (FR-F-4, FR-F-5, D-72, D-73). The files go to tests/golden/seed/,
the page data (ui-spec.md §7) to frontend/tests/fixtures/seed/ with a fixed `approved_at`, the one
value that follows the clock. `test_seed.py` fails when a fixture no longer matches the backend;
rewrite them with

    uv run python tests/seed_fixtures.py        (from backend/)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

if __name__ == "__main__":  # run as a script, the backend package is beside tests/, not on the path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from report_fixtures import sample_builds  # noqa: E402
from seedfoundry import package  # noqa: E402
from seedfoundry.generate.layers import NAMES  # noqa: E402
from seedfoundry.state import Approval, State  # noqa: E402

GOLDEN_DIR = Path(__file__).resolve().parent / "golden" / "seed"
PAGE_DIR = Path(__file__).resolve().parents[2] / "frontend" / "tests" / "fixtures" / "seed"
APPROVED_AT = "2026-10-04T12:00:00.000+00:00"
PATHS = (1, 2)


def approved_state(iteration: int) -> State:
    """The lab just after Approve on the sample's iteration `iteration` report."""
    first, second = sample_builds()
    builds = [first.model_copy(deep=True)] + ([second.model_copy(deep=True)] if iteration == 2 else [])
    chosen = builds[-1]
    return State(iteration=iteration, builds=builds, approval=Approval(iteration=iteration, build_id=chosen.id, approved_at=APPROVED_AT))


def files(iteration: int) -> dict[str, str]:
    return package.seed_files(*package.approved(approved_state(iteration)))


def page(iteration: int) -> str:
    return json.dumps(package.page(approved_state(iteration)), indent=1, ensure_ascii=False) + "\n"


def fixtures() -> dict[Path, str]:
    """Every fixture path and the text it should hold."""
    out: dict[Path, str] = {}
    for iteration in PATHS:
        made = files(iteration)
        for name in NAMES:
            out[GOLDEN_DIR / f"iteration-{iteration}" / name] = made[name]
        out[PAGE_DIR / f"iteration-{iteration}.json"] = page(iteration)
    return out


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    for path, text in fixtures().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {path.relative_to(root).as_posix()}")


if __name__ == "__main__":
    main()
