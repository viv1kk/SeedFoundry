"""License Optimization dashboard: the descriptor, the query engine and the payload built from the
seat rows (FR-D-1 to FR-D-6, D-56), and iteration 1's defect overlay (overlay.py, D-13, D-60)."""

from __future__ import annotations

from typing import Any

from seedfoundry.dashboard import overlay
from seedfoundry.dashboard.descriptor import DASHBOARD_ID, descriptor
from seedfoundry.dashboard.payload import build
from seedfoundry.dashboard.query import Drill, QueryError, parse
from seedfoundry.data import dataset

DEFAULT_DATASET = "primary"


def dashboard(iteration: int, dataset_name: str = DEFAULT_DATASET, drill: str | None = None, page: int = 1, sort: str | None = None, direction: str | None = None) -> dict[str, Any]:
    """The descriptor and payload for one iteration's dashboard at one drill level."""
    desc = descriptor(iteration)
    payload = build(desc, dataset(dataset_name), drill, page, sort, direction)
    return {"id": DASHBOARD_ID, "iteration": iteration, "variant": desc["variant"], "descriptor": desc, "payload": payload}


__all__ = ["DASHBOARD_ID", "DEFAULT_DATASET", "Drill", "QueryError", "build", "dashboard", "descriptor", "overlay", "parse"]
