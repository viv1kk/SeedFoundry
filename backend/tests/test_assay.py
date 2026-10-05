"""M5: Assay statistics (requirements §2, real): Ensemble sections, coverage, statements,
the Seed name (OQ-7), the fingerprint, and T-01's rule (D-42 (a))."""

from __future__ import annotations

from seedfoundry.intake import assay
from seedfoundry.sample import sample_files
from seedfoundry.state import CORE_CATEGORIES, Category, IntakeFile
from test_sample import ensemble_sections

NAMES = {
    Category.PERSON: "Identity.md",
    Category.INSTRUMENT_AWARENESS: "Tools_and_Skills.md",
    Category.ENVIRONMENT: "Environment_01.md",
    Category.MUSIC: "Value_0001.md",
}


def sample() -> list[IntakeFile]:
    return [IntakeFile(id=f"f-{n}", name=name, category=c, content=text) for n, (name, c, text) in enumerate(sample_files(), 1)]


def file(category: Category, content: str, name: str | None = None, id: str = "f-1") -> IntakeFile:
    return IntakeFile(id=id, name=name or NAMES.get(category, "notes.md"), category=category, content=content)


def test_section_lists_match_the_ensemble_doc():
    doc = ensemble_sections()
    for category in CORE_CATEGORIES:
        assert list(assay.ENSEMBLE_SECTIONS[category]) == doc[NAMES[category]], category


def test_the_sample_covers_every_section():
    for f in sample():
        if f.category in CORE_CATEGORIES:
            result = assay.coverage(f)
            assert result.percent == 100 and result.missing == [], f.name


def test_coverage_reads_level_two_headings_only_and_ignores_case():
    text = "# Music\n\n## purpose\n\nx\n\n### Core Principles\n\ny\n\n## Decision Logic:\n"
    result = assay.coverage(file(Category.MUSIC, text))
    assert result.found == ["Purpose", "Decision Logic"]
    assert result.missing == ["Core Principles", "Value Logic"]
    assert result.percent == 50


def test_headings_inside_code_fences_do_not_count():
    text = "# Music\n\n```\n## Purpose\n```\n"
    assert assay.coverage(file(Category.MUSIC, text)).found == []


def test_statements_count_list_items_else_paragraphs():
    assert assay.statements(["- a", "  - b", "1. c", "text"]) == 3
    assert assay.statements(["One paragraph", "still it", "", "Two"]) == 2
    assert assay.statements([]) == 0


def test_section_lines_include_sub_headings():
    text = "## Core Principles\n\n### Filtering\n\n- a\n- b\n\n## Value Logic\n\n- c\n"
    lines = assay.section_lines(text, "Core Principles")
    assert assay.statements(lines) == 2
    assert "### Filtering" in lines
    assert assay.section_lines(text, "Purpose") is None


def test_seed_name_is_the_first_heading_of_music():
    music = next(f for f in sample() if f.category == Category.MUSIC)
    assert assay.seed_name(music) == "License Optimization"
    assert assay.seed_name(file(Category.MUSIC, "no heading here")) == "Untitled Seed"
    assert assay.seed_name(None) == "Untitled Seed"


def test_fingerprint_follows_content_not_ids_or_order():
    files = sample()
    renumbered = [f.model_copy(update={"id": f"x-{n}"}) for n, f in enumerate(reversed(files))]
    assert assay.digest(renumbered) == assay.digest(files)
    changed = [f.model_copy(update={"content": f.content + " "}) if f.category == Category.MUSIC else f for f in files]
    assert assay.digest(changed) != assay.digest(files)
    assert assay.fingerprint(files) == assay.digest(files)[:6]


def test_a_whitespace_only_core_file_counts_as_missing():
    # D-42 (a): the same rule as the Knowledge checklist.
    files = [file(c, "# x\n", id=f"f-{n}") for n, c in enumerate(CORE_CATEGORIES)]
    files[1] = file(Category.INSTRUMENT_AWARENESS, " \n\t\n", id="f-1")
    inventory = assay.inventory(files)
    assert inventory.missing == [Category.INSTRUMENT_AWARENESS]
    assert [f.category for f in inventory.core] == [Category.PERSON, Category.ENVIRONMENT, Category.MUSIC]


def test_inventory_of_the_sample():
    inventory = assay.inventory(sample())
    assert [f.name for f in inventory.core] == list(NAMES.values())
    assert [f.name for f in inventory.context] == []  # no Misc Context since D-84
    assert inventory.missing == []
    assert inventory.total_bytes == sum(len(text.encode("utf-8")) for _, _, text in sample_files())
