# Seed v0.1 --- Documents

Seed v0.1 is a deterministic, offline simulation of a methodology-driven
analytical system: a seed is planted, it discovers a client environment,
assesses what analysis the evidence supports, asks a person at the
boundaries that matter, builds what was approved, and then runs it as
Agent One VW, collecting and recalibrating. No model is called anywhere.
"Systems" is the project's working name, kept in the older documents'
titles (D-11).

The build is complete through M22 and was accepted as final on
2026-10-02.

## The documents

| Document | What it is | Read it to |
| -------- | ---------- | ---------- |
| `requirements.md` | The V1 requirements, as amended | Know what the system must do |
| `decisions.md` | Every ruling, measurement and amendment, D-1 to D-22 and A-1 to A-16 | Know why it is built this way |
| `implementation-plan.md` | The milestone plan, M0 to M22, with the architecture summary | Know how it was built, and in what order |
| `project-notes.md` | §§1--82: the product vision. §83: the first V1 specification. §84: the Seeding and Life rework, and the build log of every milestone since M11 | Understand the intent, and what each milestone changed |
| `architecture.md` | The system as built: lifecycle, run, events, API, analytics, protection, tests | Work on the code |
| `design-system.md` | The visual language as built: tokens, type, layout, motion, contrast | Change anything on screen |
| `operator-guide.md` | Setup, controls, the demo step by step, rehearsal, troubleshooting | Run or present the demo |

## Which document wins

1. **The code**, for what the system does today. The as-built documents
   (`architecture.md`, `design-system.md`, `operator-guide.md`) describe
   it and are corrected when they drift.
2. **`requirements.md`** over `project-notes.md`, all of it.
3. **`decisions.md`** over `implementation-plan.md`.

Superseded requirements and rulings are struck through or marked, and
left in place, so the record of why something changed survives.
`decisions.md` §8 lists where the build departs from an earlier
ruling's wording.

## Elsewhere in the repository

- `seeds/core.md`, `seeds/adaptation.md`, `seeds/protection.md`: the
  seed itself, a deliverable in its own right (FR-S1).
  `seeds/protection.md` is held equal to the enforced rule set by a test.
- `run.ps1` and `run.py`: the launchers. See `operator-guide.md` §1.
