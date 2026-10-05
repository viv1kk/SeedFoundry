"""M10: observer feedback routed into the four core files (FR-RB-7, A-4, D-36, D-68). Each rule set
sends a segment to the right file and section; ties break in the fixed order; an unmatched segment
changes no file; the same feedback gives the same edits; segments are appended verbatim under the
feedback heading, which is created when missing; the demo's feedback reaches all four files and
raises no boundary advisory."""

from __future__ import annotations

import difflib

import pytest

from seedfoundry.intake import boundary
from seedfoundry.intake.feedback import FEEDBACK_NAME
from seedfoundry.intake.routing import HEADING, TARGETS, place, route
from seedfoundry.sample import demo_feedback, sample_files
from seedfoundry.state import CORE_CATEGORIES, Category, IntakeFile, next_version
from test_no_em_dash import em_dashes


def sample() -> list[IntakeFile]:
    return [IntakeFile(id=f"f-{n}", name=name, category=c, content=text) for n, (name, c, text) in enumerate(sample_files(), 1)]


def with_feedback(text: str, files: list[IntakeFile] | None = None) -> list[IntakeFile]:
    return [*(files or sample()), IntakeFile(id="f-99", name=FEEDBACK_NAME, category=Category.MISC_CONTEXT, content=text)]


def by_name(files: list[IntakeFile]) -> dict[str, str]:
    return {f.name: f.content for f in files}


# One segment per rule set, each in its own words: (segment, file after routing, section). A routed
# file with a versioned name steps to its next version (D-85).
PLANTED = [
    ("The pie has too many slices and the colours are off the palette.", "Environment_02.md", "Styling"),
    ("The spinner keeps the panel waiting for seconds.", "Environment_02.md", "User Experience"),
    ("The totals do not add up to the seat records.", "Environment_02.md", "Data Layer"),
    ("Assignee names need privacy: check every export before it leaves the sandbox.", "Environment_02.md", "Protection Layer"),
    ("The language model can hallucinate a number.", "Tools_and_Skills.md", "Model Behaviour"),
    ("State each assumption and the evidence behind the reasoning.", "Identity.md", "Reasoning methods"),
    ("Prioritise by recoverable cost and rank products by score.", "Value_0002.md", "Core Principles"),
    ("Decide between choices by the decision rules.", "Value_0002.md", "Decision Logic"),
    ("Success is the value of the savings, not their size.", "Value_0002.md", "Value Logic"),
]


def test_every_target_has_a_planted_segment_and_the_order_is_d36s():
    assert [(t.category, t.section) for t in TARGETS] == [
        (Category.ENVIRONMENT, "Styling"),
        (Category.ENVIRONMENT, "User Experience"),
        (Category.ENVIRONMENT, "Data Layer"),
        (Category.ENVIRONMENT, "Protection Layer"),
        (Category.INSTRUMENT_AWARENESS, "Model Behaviour"),
        (Category.PERSON, "Reasoning methods"),
        (Category.MUSIC, "Core Principles"),
        (Category.MUSIC, "Decision Logic"),
        (Category.MUSIC, "Value Logic"),
    ]
    assert [section for _, _, section in PLANTED] == [t.section for t in TARGETS]


def test_routing_reuses_the_boundary_lints_rule_sets():
    lint = {p.regex.pattern for rule in boundary.RULES for p in rule.patterns}
    routed = {p.pattern for t in TARGETS for p in t.patterns}
    assert lint <= routed  # every lint pattern routes to the home it suggests


@pytest.mark.parametrize(("segment", "name", "section"), PLANTED, ids=[s for _, _, s in PLANTED])
def test_each_rule_set_sends_a_segment_to_its_file_and_section(segment, name, section):
    routed = route(with_feedback(segment))
    placed = routed.placements[0]
    assert (placed.target.section, routed.changes[placed.target.category].after.name) == (section, name)
    after = by_name(routed.files)[name]
    assert f"### {HEADING}\n\n{segment}\n" in after
    # The other three core files are untouched.
    before = by_name(sample())
    assert [n for n in by_name(routed.files) if by_name(routed.files)[n] != before.get(n) and n != FEEDBACK_NAME] == [name]
    # Routing by the boundary rules keeps the routed file boundary-clean.
    assert boundary.lint(routed.files) == []


@pytest.mark.parametrize(
    ("segment", "winner"),
    [
        ("The chart total is wrong.", "Styling"),  # Styling (chart) ties Data Layer (total)
        ("The panel total is wrong.", "User Experience"),  # User Experience (panel) ties Data Layer (total)
        ("The total needs a check.", "Data Layer"),  # Data Layer (total) ties Protection Layer (check)
        ("Check the model.", "Protection Layer"),  # Protection Layer (check) ties Model Behaviour (the model)
        ("The model needs evidence.", "Model Behaviour"),  # Model Behaviour ties person.md (evidence)
        ("Evidence over value.", "Reasoning methods"),  # person.md ties music.md (value)
        ("Rank the choices.", "Core Principles"),  # Core Principles (rank) ties Decision Logic (choices)
        ("Choose by value.", "Decision Logic"),  # Decision Logic (choose) ties Value Logic (value)
    ],
)
def test_ties_break_in_the_fixed_order(segment, winner):
    placed = place(1, segment)
    scores = {t.section: sum(1 for p in t.patterns if p.search(segment)) for t in TARGETS}
    top = max(scores.values())
    tied = [section for section, n in scores.items() if n == top]
    assert len(tied) == 2 and winner == tied[0]  # a real tie, and the winner comes first in D-36's order
    assert placed.target.section == winner


def test_more_matches_beat_the_fixed_order():
    # One Styling word against three Data Layer words: Data Layer wins despite coming later.
    assert place(1, "The chart totals do not add up to the seat records.").target.section == "Data Layer"


def test_an_unmatched_segment_changes_no_file():
    routed = route(with_feedback("Otherwise the build was easy to follow."))
    assert routed.placements[0].target is None and routed.kept == routed.placements
    assert all(not change.changed for change in routed.changes.values())
    assert by_name(routed.files) == by_name(with_feedback("Otherwise the build was easy to follow."))


def test_without_feedback_nothing_changes():
    routed = route(sample())
    assert routed.feedback is None and routed.placements == []
    assert by_name(routed.files) == by_name(sample())


def test_the_same_feedback_gives_the_same_edits():
    feedback = demo_feedback()
    one, two = route(with_feedback(feedback)), route(with_feedback(feedback))
    assert by_name(one.files) == by_name(two.files)
    assert [(p.number, p.target and p.target.section, p.matched) for p in one.placements] == [
        (p.number, p.target and p.target.section, p.matched) for p in two.placements
    ]
    # Routed again over its own result (a rerun of iteration 2), nothing is added twice.
    again = route(one.files)
    assert by_name(again.files) == by_name(one.files)
    assert all(s.present and not s.segments for c in again.changes.values() for s in c.sections)


def test_segments_are_appended_verbatim_at_the_end_of_their_section():
    routed = route(with_feedback("- Use a bar chart, not a pie.\n\nThe colours\nare off the palette.\n"))
    environment = by_name(routed.files)["Environment_02.md"]
    styling = environment.split("\n## Styling\n", 1)[1].split("\n## Adaptation Layer\n", 1)[0]
    assert styling.endswith(f"### {HEADING}\n\n- Use a bar chart, not a pie.\n\nThe colours\nare off the palette.\n")
    # Everything that was there stays, in order: the edit only inserts.
    original = by_name(sample())["Environment_01.md"].split("\n")
    ops = difflib.SequenceMatcher(a=original, b=environment.split("\n"), autojunk=False).get_opcodes()
    assert {op for op, *_ in ops} == {"equal", "insert"}


def test_a_missing_section_and_heading_are_created():
    files = sample()
    person = next(f for f in files if f.category == Category.PERSON)
    person.content = "# Person\n\n## Domain expertise\n\n- Licensing.\n"
    routed = route(with_feedback("Name the evidence for every claim.", files))
    change = routed.changes[Category.PERSON]
    assert [(s.section, s.created, s.segments) for s in change.sections] == [("Reasoning methods", True, [1])]
    assert change.after.content == (
        "# Person\n\n## Domain expertise\n\n- Licensing.\n\n## Reasoning methods\n\n"
        f"### {HEADING}\n\nName the evidence for every claim.\n"
    )


def test_lines_added_are_the_lines_the_diff_inserts():
    routed = route(with_feedback(demo_feedback()))
    for change in routed.changes.values():
        before, after = change.before.content.split("\n"), change.after.content.split("\n")
        ops = difflib.SequenceMatcher(a=before, b=after, autojunk=False).get_opcodes()
        assert {op for op, *_ in ops} <= {"equal", "insert"}  # nothing removed or rewritten
        inserted = sum(j2 - j1 for op, _, _, j1, j2 in ops if op == "insert")
        assert inserted == change.lines_added == sum(s.lines_added for s in change.sections)


def test_the_demo_feedback_reaches_all_four_files_and_raises_no_advisory():
    text = demo_feedback()
    assert em_dashes(text) == []
    routed = route(with_feedback(text))
    assert {p.target.category for p in routed.routed} == set(CORE_CATEGORIES)
    assert all(change.changed for change in routed.changes.values())
    assert boundary.lint(routed.files) == []
    assert [p.number for p in routed.kept] == [len(routed.placements)]  # one segment fits no file
    # It cites the finding ids, so the observer's words point at the report.
    for finding in ("N-1", "N-5", "V-1", "V-8", "L-1"):
        assert finding in text


# Versioned names (D-85)


def test_a_versioned_name_steps_up_when_the_feedback_changes_the_file():
    assert [next_version(n) for n in ("Environment_01.md", "Value_0001.md", "Environment_09.md", "Value_9999.md")] == [
        "Environment_02.md",
        "Value_0002.md",
        "Environment_10.md",
        "Value_10000.md",
    ]
    assert [next_version(n) for n in ("Identity.md", "Tools_and_Skills.md", "environment.md")] == [
        "Identity.md",
        "Tools_and_Skills.md",
        "environment.md",
    ]
    routed = route(with_feedback("The totals do not add up to the seat records."))
    names = {c: change.after.name for c, change in routed.changes.items()}
    assert names == {
        Category.PERSON: "Identity.md",
        Category.INSTRUMENT_AWARENESS: "Tools_and_Skills.md",
        Category.ENVIRONMENT: "Environment_02.md",  # changed, so its next version
        Category.MUSIC: "Value_0001.md",  # unchanged, so the same version
    }
    # Routed again over its own result (a rerun), nothing changes, so no name steps.
    again = route(routed.files)
    assert {c: change.after.name for c, change in again.changes.items()} == names


def test_a_name_without_a_number_is_kept_when_the_file_changes():
    files = [f.model_copy(update={"name": "environment.md"}) if f.category == Category.ENVIRONMENT else f for f in sample()]
    routed = route(with_feedback("The totals do not add up to the seat records.", files))
    assert routed.changes[Category.ENVIRONMENT].changed and routed.changes[Category.ENVIRONMENT].after.name == "environment.md"
