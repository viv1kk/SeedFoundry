# SeedFactory docs

SeedFactory is a deterministic, offline, no-LLM simulation of a lab that takes Ensemble knowledge files, builds them into a Seed, runs and validates the Seed in a simulated sandbox, and improves it through one round of human feedback.

## Document table

| File | Purpose | Read when |
|---|---|---|
| `CLAUDE.md` | Standing rules for every Claude Code session | Every session (auto-loaded via root `CLAUDE.md`) |
| `KICKOFF_PROMPT.md` | First-session prompt (M0) | Once, at kickoff |
| `project-notes.md` | Vision, origin, glossary, build log | First, for the why |
| `requirements.md` | Binding spec: goals, scope, FRs, NFRs, acceptance | Before any feature work |
| `ui-spec.md` | The four screens, the demo controller, the rebuild modal | Before any frontend work |
| `build-simulation.md` | Phase catalogue, log format, timing budget, planted defects, validators, generated files | Before engine, report or dashboard work |
| `decisions.md` | Rulings (D-n), open questions (OQ-n), risks (R-n), the as-built reconciliation (§4, M13) | When something seems arbitrary |
| `implementation-plan.md` | Milestones M0 to M13, repo layout, critical path | At the start of every session |
| `methodology.md` | Working method, build log format, gates | Once, then as needed |
| `seed-reuse-notes.md` | Written in M0: what is reused from Seed v0.1 and where it lives | Before reusing anything |
| `operator-guide.md` | Written in M12: set up, start, controls, the timed demo script, rehearsing, checks before a demo, troubleshooting | Before presenting or rehearsing |
| `ensemble/ensemble_context.md` | The Ensemble architecture: what the four knowledge files are | Before intake, Assay or file generation work |
| `seed_docs/` | Seed v0.1 reference docs (prior project) | Reference only; never edited |

## Precedence (when docs disagree)

1. The code > as-built notes in any doc.
2. `requirements.md` (with amendments) > `ui-spec.md` and `build-simulation.md` > `project-notes.md`.
3. `decisions.md` > `implementation-plan.md`.
4. Any SeedFactory doc > `seed_docs/` for SeedFactory behaviour. `seed_docs/` wins only on what Seed v0.1 itself was (its data, its dashboard, its lifecycle, its visual language).

Struck-through text is superseded and kept for history.
