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


# The demo's observer feedback (FR-DC-2 Prefill, build-simulation.md §9): plain words citing the
# finding ids, written so that routing (D-36) reaches all four core files and raises no boundary
# advisory. In its own folder, so it is never loaded as part of the sample Seed.
DEMO_FEEDBACK = SAMPLE_DIR / "rebuild" / "observer-feedback-iteration-1.md"
# The demo's feedback on any later iteration, which has no findings to cite: refinements, written
# like the first so that routing reaches the core files and raises no boundary advisory (D-81).
DEMO_REFINEMENT = SAMPLE_DIR / "rebuild" / "observer-feedback-later.md"


def demo_feedback(rejected: int = 1) -> str:
    return normalise((DEMO_FEEDBACK if rejected <= 1 else DEMO_REFINEMENT).read_text(encoding="utf-8"))


def sample_files() -> list[tuple[str, Category, str]]:
    """(name, category, content) for each sample file, in load order."""
    return [(name, category, normalise((SAMPLE_DIR / name).read_text(encoding="utf-8"))) for name, category in SAMPLE_FILES]
