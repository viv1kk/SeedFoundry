"""No em dashes (D-20, NFR-8), from M3 on: in frontend source (templates and strings),
backend source, the tests, the launchers and SeedFactory's own docs.

docs/seed_docs/ is Seed v0.1's reference material, kept as it was written, so it is not
scanned (docs/CLAUDE.md rule 4). From M11 generated output is scanned too (D-44): the golden Seed
files sit in tests/golden/ and so in the scan, and the files and zip of both approval paths are
generated and scanned here, the zip's contents read back from its bytes.

The patterns are built from parts so this file does not match itself.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SCANNED = [
    ROOT / "CLAUDE.md",
    ROOT / "run.py",
    ROOT / "run.ps1",
    ROOT / "docs",
    ROOT / "backend" / "seedfoundry",
    ROOT / "backend" / "tests",
    ROOT / "backend" / "pyproject.toml",
    ROOT / "frontend" / "src",
    ROOT / "frontend" / "tests",
    ROOT / "frontend" / "scripts",
    ROOT / "frontend" / "index.html",
    ROOT / "frontend" / "vite.config.ts",
    ROOT / "frontend" / "package.json",
]
EXCLUDED = [ROOT / "docs" / "seed_docs"]
SUFFIXES = {".py", ".ps1", ".md", ".ts", ".js", ".vue", ".html", ".css", ".json", ".toml", ".txt"}

# The character itself, and the ways source can spell it: HTML entities and a JS or Python escape.
EM_DASH = re.compile(
    "|".join(
        [
            re.escape(chr(0x2014)),
            "&" + "mdash;",
            "&#" + "8212;",
            "&#[xX]" + "2014;",
            re.escape("\\" + "u2014"),
        ]
    )
)


def scanned_files() -> list[Path]:
    found = []
    for path in SCANNED:
        if path.is_file():
            found.append(path)
        elif path.is_dir():
            found += [
                p
                for p in path.rglob("*")
                if p.is_file()
                and p.suffix in SUFFIXES
                and "__pycache__" not in p.parts
                and not any(p.is_relative_to(excluded) for excluded in EXCLUDED)
            ]
    return found


def em_dashes(text: str) -> list[int]:
    """Line numbers (from 1) of every line holding an em dash."""
    return [n for n, line in enumerate(text.splitlines(), 1) if EM_DASH.search(line)]


def test_the_scan_covers_frontend_backend_and_docs():
    names = {p.relative_to(ROOT).as_posix() for p in scanned_files()}
    for expected in (
        "docs/requirements.md",
        "docs/ensemble/ensemble_context.md",
        "backend/seedfoundry/main.py",
        "frontend/src/main.ts",
        "frontend/src/views/KnowledgeView.vue",
        "frontend/tests/fixtures/hostile.md",
    ):
        assert expected in names
    assert not any(name.startswith("docs/seed_docs/") for name in names)


def test_the_check_finds_every_spelling():
    for text in (chr(0x2014), "a &" + "mdash; b", "&#" + "8212;", "&#x" + "2014;", "'\\" + "u2014'"):
        assert em_dashes(text) == [1], text
    # An en dash and a hyphen are fine.
    assert em_dashes("1" + chr(0x2013) + "2, a-b") == []


def test_no_em_dash_anywhere():
    offenders = []
    for path in scanned_files():
        for line in em_dashes(path.read_text(encoding="utf-8")):
            offenders.append(f"{path.relative_to(ROOT).as_posix()}:{line}")
    assert offenders == []


def test_no_em_dash_in_the_generated_seed_files_or_their_zip():
    import io
    import zipfile

    from seed_fixtures import PATHS, approved_state
    from seedfoundry import package

    offenders = []
    for iteration in PATHS:
        state = approved_state(iteration)
        made = package.seed_files(*package.approved(state))
        archive = zipfile.ZipFile(io.BytesIO(package.zip_bytes(made)))
        texts = {f"iteration {iteration}: {n}": t for n, t in made.items()}
        texts |= {f"iteration {iteration} zip: {n}": archive.read(n).decode("utf-8") for n in archive.namelist()}
        texts[f"iteration {iteration}: page"] = str(package.page(state))
        for where, text in texts.items():
            offenders += [f"{where}:{line}" for line in em_dashes(text)]
    assert offenders == []
