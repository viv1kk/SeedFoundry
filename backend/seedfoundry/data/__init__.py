"""License Optimization datasets, primary and alternate (D-30, D-55): SeedFoundry's own estates
from a seeded generator, following Seed v0.1's methodology (seed-reuse-notes.md §5.7)."""

from seedfoundry.data.generate import DATASETS, SEED_RULE, dataset, generate
from seedfoundry.data.model import (
    CLASS_LABELS,
    CLASS_ROLES,
    CLASSES,
    RECOVERABLE,
    TEST_ORDER,
    Dataset,
    Product,
    Seat,
    classify,
)

__all__ = [
    "CLASSES",
    "CLASS_LABELS",
    "CLASS_ROLES",
    "DATASETS",
    "RECOVERABLE",
    "SEED_RULE",
    "TEST_ORDER",
    "Dataset",
    "Product",
    "Seat",
    "classify",
    "dataset",
    "generate",
]
