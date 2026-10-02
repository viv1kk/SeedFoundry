"""Fixed addresses for the two processes (OQ-8: 8100 and 5273 so SeedFoundry can run beside Seed v0.1),
and where runtime data lives (D-3)."""

import os
from pathlib import Path

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8100
FRONTEND_PORT = 5273

ROOT = Path(__file__).resolve().parents[2]


def var_dir() -> Path:
    """var/ at the repository root. SEEDFOUNDRY_VAR_DIR points elsewhere (tests use it)."""
    return Path(os.environ.get("SEEDFOUNDRY_VAR_DIR") or ROOT / "var")
