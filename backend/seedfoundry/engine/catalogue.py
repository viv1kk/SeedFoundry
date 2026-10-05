"""The phase catalogue (build-simulation.md §2, D-17, D-26): eleven phases in order, their
weights, sub-steps and tests. Weights sum to 100 and map to a 75 s budget at 1x (D-7),
so one unit is 0.75 s of simulated time.

Count, order, weights and test ids are fixed unless the catalogue is amended. Sub-step
names are as built in M5 (build-simulation.md §2, as-built note).
"""

from __future__ import annotations

from dataclasses import dataclass

from seedfoundry.state import PhasePlan, PlanItem

BUDGET_SECONDS = 75.0
TOTAL_WEIGHT = 100


@dataclass(frozen=True)
class Step:
    id: str
    name: str
    # A rebuild step runs in every iteration after the first, which each start from the observer
    # feedback that rejected the iteration before (D-36, D-81).
    rebuild: bool = False


@dataclass(frozen=True)
class Phase:
    id: str
    name: str
    weight: int
    steps: tuple[Step, ...]
    tests: tuple[tuple[str, str], ...]

    @property
    def seconds(self) -> float:
        return BUDGET_SECONDS * self.weight / TOTAL_WEIGHT

    def steps_for(self, iteration: int) -> list[Step]:
        return [step for step in self.steps if not step.rebuild or iteration >= 2]


REBUILD = True

PHASES: tuple[Phase, ...] = (
    Phase(
        "assay",
        "Assay",
        6,
        (
            # Apply observer feedback (FR-RB-7, FR-RB-8, D-36): iteration 2 on, before anything else (D-81).
            Step("feedback-route", "Route feedback to Ensemble files", REBUILD),
            Step("feedback-person", "Update Identity.md", REBUILD),
            Step("feedback-instrument", "Update Tools_and_Skills.md", REBUILD),
            Step("feedback-environment", "Update Environment.md", REBUILD),
            Step("feedback-music", "Update Value.md", REBUILD),
            Step("inventory", "Inventory files"),
            Step("coverage", "Measure Ensemble coverage per file"),
            Step("boundary", "Ensemble boundary check"),
            Step("fingerprint", "Fingerprint intake"),
        ),
        (("T-01", "Initiation files present"), ("T-02", "Ensemble coverage"), ("T-03", "Ensemble boundary check")),
    ),
    Phase(
        "distill",
        "Distillation",
        12,
        (
            Step("profile", "Load model profile from Tools_and_Skills.md"),
            Step("budget", "Plan context budget"),
            Step("music", "Distil Value.md"),
            Step("person", "Distil Identity.md"),
            Step("environment", "Distil Environment.md layers"),
            Step("context", "Merge context notes"),
            Step("feedback", "Ingest observer feedback and prior findings", REBUILD),
        ),
        (("T-04", "All Value.md sections extracted"),),
    ),
    Phase(
        "synth",
        "Synthesis",
        10,
        (
            Step("core", "Draft core.md"),
            Step("adaptation", "Draft adaptation.md"),
            Step("protection", "Draft protection.md"),
            Step("manifest", "Assemble Seed manifest"),
        ),
        (("T-05", "Manifest schema valid"),),
    ),
    Phase(
        "xexam",
        "Cross-Examination",
        8,
        (
            Step("core", "Reviewer pass on core"),
            Step("layers", "Reviewer pass on adaptation and protection"),
            Step("resolve", "Resolve contradictions"),
            Step("signoff", "Sign off drafts"),
        ),
        (("T-06", "No contradictions between files"),),
    ),
    Phase(
        "germ",
        "Germination Trial",
        8,
        (
            Step("dry-run", "Dry run on micro dataset"),
            Step("data-swap", "Data-swap test on alternate dataset"),
            Step("shape", "Output shape check"),
        ),
        (("T-07", "Dry run completes"), ("T-08", "Data-swap logic unchanged")),
    ),
    Phase(
        "contain",
        "Containment",
        7,
        (
            Step("handshake", "Seed API handshake"),
            Step("sandbox", "Provision isolated sandbox"),
            Step("upload", "Upload seed files"),
            Step("checksums", "Verify upload checksums"),
        ),
        (("T-09", "Upload checksums match"),),
    ),
    Phase(
        "plant",
        "Planting",
        8,
        (
            Step("layers", "Plant the three layers"),
            Step("headings", "Heading summary per layer"),
            Step("stack", "List the declared stack"),
        ),
        (("T-10", "Seed reports ready"),),
    ),
    Phase(
        "seeding",
        "Seeding & Life",
        16,
        (
            Step("discovery", "Discovery"),
            Step("assessment", "Assessment"),
            Step("implementation", "Implementation"),
            Step("cleanup", "Cleanup"),
            Step("life", "Life"),
        ),
        (("T-11", "All gates resolved"), ("T-12", "Outputs produced")),
    ),
    Phase(
        "probe",
        "Stress & Probe",
        9,
        (
            Step("protection", "Protection rule probes"),
            Step("malformed", "Malformed input probes"),
            Step("latency", "Panel latency measurement"),
        ),
        (("T-13", "Protection probes"), ("T-14", "Malformed input rejected"), ("T-15", "Latency within budget")),
    ),
    Phase(
        "harvest",
        "Harvest Validation",
        10,
        (
            Step("collect", "Collect dashboard payload"),
            Step("numeric", "Numeric reconciliation"),
            Step("chart", "Chart and data consistency"),
            Step("visual", "Visual QA"),
            Step("contrast", "Contrast check"),
        ),
        (
            ("T-16", "Numeric reconciliation"),
            ("T-17", "Chart fitness"),
            ("T-18", "Format and label consistency"),
            ("T-19", "Palette and layout"),
            ("T-20", "Contrast"),
        ),
    ),
    Phase(
        "report",
        "Teardown & Report",
        6,
        (
            Step("teardown", "Tear down sandbox"),
            Step("compile", "Compile report"),
            Step("package", "Package seed files"),
        ),
        (("T-21", "Sandbox torn down cleanly"),),
    ),
)

TEST_NAMES = {test_id: name for phase in PHASES for test_id, name in phase.tests}


def plan(iteration: int) -> list[PhasePlan]:
    """The phases, sub-steps and tests of one iteration, as the build record keeps them."""
    return [
        PhasePlan(
            id=phase.id,
            name=phase.name,
            weight=phase.weight,
            steps=[PlanItem(id=f"{phase.id}.{step.id}", name=step.name) for step in phase.steps_for(iteration)],
            tests=[PlanItem(id=test_id, name=name) for test_id, name in phase.tests],
        )
        for phase in PHASES
    ]
