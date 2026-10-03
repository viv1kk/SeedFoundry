"""Real build reports, and the sample build's kept events, for the frontend's tests
(frontend/tests/fixtures/reports/).

The sample Seed is built for iteration 1, then iteration 2 by API, with the real engine on a fake
clock in a temporary var/, and each build's report is written as the backend serves it (D-64),
with the iteration 1 build's kept events beside it. The frontend's fake server replays them, so
its report tests read what the backend assembles. `test_report.py` fails when a fixture no longer
matches the backend; rewrite them with

    uv run python tests/report_fixtures.py        (from backend/)
"""

from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from functools import cache
from pathlib import Path

if __name__ == "__main__":  # run as a script, the backend package is beside tests/, not on the path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from seedfoundry import demo, report  # noqa: E402
from seedfoundry.engine.clock import FakeClock  # noqa: E402
from seedfoundry.engine.runner import BuildEngine  # noqa: E402
from seedfoundry.state import Build, StateManager  # noqa: E402

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "frontend" / "tests" / "fixtures" / "reports"
NAMES = ("iteration-1.json", "iteration-2.json", "iteration-1-events.json")


@cache
def sample_builds() -> tuple[Build, Build]:
    """The sample's iteration 1 and iteration 2 builds, completed, in a throwaway var/."""

    async def go() -> tuple[Build, Build]:
        with tempfile.TemporaryDirectory() as var:
            manager = StateManager.open(Path(var))
            manager.apply(demo.load_sample())
            engine = BuildEngine(manager, FakeClock(True))
            engine.start()
            await engine.wait()
            engine.start(2)
            await engine.wait()
            first, second = manager.state.builds
            return first.model_copy(deep=True), second.model_copy(deep=True)

    return asyncio.run(go())


def render(name: str) -> str:
    first, second = sample_builds()
    if name == "iteration-1-events.json":
        # wall_ts is the one value that differs between runs (NFR-1), so the fixture fixes it.
        body = [{**e.model_dump(mode="json"), "wall_ts": "2026-10-03T12:00:00.000+00:00"} for e in first.log]
    else:
        body = report.assemble(first if name == "iteration-1.json" else second)
    return json.dumps(body, indent=1, ensure_ascii=False) + "\n"


def main() -> None:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    for name in NAMES:
        (FIXTURE_DIR / name).write_text(render(name), encoding="utf-8", newline="\n")
        print(f"wrote reports/{name}")


if __name__ == "__main__":
    main()
