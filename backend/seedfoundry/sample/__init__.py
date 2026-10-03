"""The sample Seed (FR-DC-3, build-simulation.md §8): four License Optimization
files and one Misc Context file, written for SeedFoundry and Ensemble-clean.
Load sample Seed puts exactly these into intake, in this order (D-46).

Line ends are normalised on reading, so the content is the same bytes on any
machine, whatever git did to the line ends on checkout (FR-DC-4, NFR-1).
"""

from __future__ import annotations

from pathlib import Path

from seedfoundry.intake.files import normalise
from seedfoundry.state import Category

SAMPLE_DIR = Path(__file__).parent

# Ensemble order, then the Misc Context file.
SAMPLE_FILES = (
    ("person.md", Category.PERSON),
    ("instrument-awareness.md", Category.INSTRUMENT_AWARENESS),
    ("environment.md", Category.ENVIRONMENT),
    ("music.md", Category.MUSIC),
    ("vendor-notes.md", Category.MISC_CONTEXT),
)


def sample_files() -> list[tuple[str, Category, str]]:
    """(name, category, content) for each sample file, in load order."""
    return [(name, category, normalise((SAMPLE_DIR / name).read_text(encoding="utf-8"))) for name, category in SAMPLE_FILES]
