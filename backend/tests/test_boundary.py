"""M5: the Ensemble boundary check (T-03, build-simulation.md §6.1, FR-T-1, D-12). Each rule
flags a planted example in a file it checks and stays quiet in the concern's home file;
the sample gives zero; findings carry file, line and suggested home."""

from __future__ import annotations

import pytest

from seedfoundry.intake.boundary import RULES, lint, lint_file
from seedfoundry.sample import sample_files
from seedfoundry.state import Category, IntakeFile

NAMES = {
    Category.PERSON: "person.md",
    Category.INSTRUMENT_AWARENESS: "instrument-awareness.md",
    Category.ENVIRONMENT: "environment.md",
    Category.MUSIC: "music.md",
    Category.MISC_CONTEXT: "notes.md",
}


def file(category: Category, content: str) -> IntakeFile:
    return IntakeFile(id="f-9", name=NAMES[category], category=category, content=content)


# Rule: (planted line, a file it is wrong in, the concern's home file, suggested home)
PLANTED = {
    "B-DATA": ("Read seat_count from the `license_seats` table, column `days_idle`.", Category.MUSIC, Category.ENVIRONMENT, "environment.md, Data Layer"),
    "B-SEC": ("Only users with admin permissions may see assignee names.", Category.PERSON, Category.ENVIRONMENT, "environment.md, Protection Layer"),
    "B-UI": ("Show unused seats in an orange colour on the treemap.", Category.MUSIC, Category.ENVIRONMENT, "environment.md, Styling"),
    "B-MODEL": ("Keep each request under 8,000 tokens.", Category.ENVIRONMENT, Category.INSTRUMENT_AWARENESS, "instrument-awareness.md, Model Behaviour or Execution Constraints"),
    "B-LOGIC": ("Prioritise products by recoverable cost, largest first.", Category.ENVIRONMENT, Category.MUSIC, "music.md, Core Principles"),
}


def test_every_rule_has_a_planted_example():
    assert sorted(PLANTED) == sorted(rule.id for rule in RULES)


@pytest.mark.parametrize("rule_id", sorted(PLANTED))
def test_each_rule_flags_its_planted_example_in_the_wrong_file(rule_id):
    line, wrong, _, home = PLANTED[rule_id]
    found = lint_file(file(wrong, f"# Title\n\n## Section\n\n{line}\n"))
    assert [(f.rule, f.line, f.home) for f in found] == [(rule_id, 5, home)]
    assert found[0].file == NAMES[wrong]
    assert found[0].excerpt == line


@pytest.mark.parametrize("rule_id", sorted(PLANTED))
def test_each_rule_stays_quiet_in_the_home_file(rule_id):
    line, _, home_file, _ = PLANTED[rule_id]
    assert [f.rule for f in lint_file(file(home_file, f"# Title\n\n{line}\n"))] == []


def test_the_sample_gives_zero():
    files = [IntakeFile(id=f"f-{n}", name=name, category=c, content=text) for n, (name, c, text) in enumerate(sample_files(), 1)]
    assert lint(files) == []


def test_panel_titles_are_allowlisted():
    # The sample's environment.md names Seed v0.1's "Optimisation candidates" panel (M4 log).
    environment = file(Category.ENVIRONMENT, "3. **Optimisation candidates:** one row per product.\n4. Optimization candidates table.\n")
    assert lint_file(environment) == []
    assert [f.rule for f in lint_file(file(Category.ENVIRONMENT, "Rank candidates by size.\n"))] == ["B-LOGIC"]


def test_one_finding_per_rule_per_line_and_several_rules_on_one_line():
    found = lint_file(file(Category.MUSIC, "Use a dark theme and a red colour, and keep within the context window.\n"))
    assert [f.rule for f in found] == ["B-UI", "B-MODEL"]


def test_misc_context_is_not_checked():
    assert lint_file(file(Category.MISC_CONTEXT, "Use red bars. Keep under 8,000 tokens. Column `seat_id`.\n")) == []


def test_findings_are_in_ensemble_order_then_by_line():
    files = [
        IntakeFile(id="f-1", name="music.md", category=Category.MUSIC, content="ok\nA pie chart.\n"),
        IntakeFile(id="f-2", name="person.md", category=Category.PERSON, content="A password.\nA theme.\n"),
    ]
    assert [(f.file, f.line, f.rule) for f in lint(files)] == [("person.md", 1, "B-SEC"), ("person.md", 2, "B-UI"), ("music.md", 2, "B-UI")]
