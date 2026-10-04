"""Loaded by Python at start when this folder is on PYTHONPATH: the rehearsal's server runs with the
offline guard (../offline.py), and every refused attempt goes to SEEDFOUNDRY_OFFLINE_LOG (D-77)."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from offline import install  # noqa: E402

install(os.environ.get("SEEDFOUNDRY_OFFLINE_LOG"))
