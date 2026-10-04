# CLAUDE.md: Standing rules for SeedFoundry

These rules apply to every session. If a doc and this file disagree, this file wins on process; `docs/requirements.md` wins on behaviour.

## What this project is

SeedFoundry is a lab that generates, tests and refines Seeds. A Seed is an Ensemble bundle (four knowledge files plus optional context) that SeedFoundry turns into a working Seed v0.1 deployment, runs in a simulated sandbox, validates, and reports on. The whole product is a deterministic, offline simulation. See `docs/project-notes.md`.

## Where things are

| Path | What it is |
|---|---|
| `docs/CLAUDE.md` | This file. Loaded every session via the one-line root `CLAUDE.md` |
| `docs/KICKOFF_PROMPT.md` | The first-session prompt (M0) |
| `docs/README.md` | Doc index and precedence rules |
| `docs/requirements.md` | Binding spec (FR, NFR, acceptance) |
| `docs/ui-spec.md` | Screens and interactions |
| `docs/build-simulation.md` | Phases, sub-steps, log format, planted defects, generated files |
| `docs/decisions.md` | Rulings, open questions, risks |
| `docs/implementation-plan.md` | Milestones, repo layout, critical path |
| `docs/methodology.md` | How work is done, logged and gated |
| `docs/project-notes.md` | Vision, history, and the build log |
| `docs/seed-reuse-notes.md` | What is reused from Seed v0.1, where it lives, the dashboard spec and defect mapping (M0) |
| `docs/ensemble/` | Ensemble architecture context |
| `docs/seed_docs/` | Seed v0.1 reference docs (prior project, read-only) |

## Hard rules

1. **No LLM, no network.** No API keys, no external calls at runtime, no CDN assets. Fonts and libraries are bundled. Simulated LLM and Seed API calls go through interfaces (`LLMClient`, `SeedClient`) with simulated implementations only.
2. **Deterministic.** Any randomness uses a seeded RNG derived from the intake content hash and iteration number. No wall-clock values in event payloads except a separate `wall_ts` field that tests ignore.
3. **Real checks, planted defects.** Iteration 1 defects are planted in the dashboard payload and styling. The validators must detect them by recomputing from source data. Never hardcode the findings list.
4. **Do not touch `docs/seed_docs/`.** It is reference only.
5. **Tests are a contract.** Never edit an existing assertion to make it pass. If an assertion is wrong, add a decision entry in `docs/decisions.md` first, then change it, and mention it in the build log.
6. **Amend, don't delete.** Requirement changes go in as amendments (A-n) with strike-through for superseded text. Decisions are never removed, only superseded.
7. **As-built honesty.** When code differs from a doc, either fix the code or update the doc with an "As built" note. Code is the final truth.
8. **One milestone at a time.** Finish the current milestone's exit criteria, update the build log, then stop and report. Do not start the next milestone without confirmation unless told to run several.
9. **Ask, don't guess, on product questions.** If a requirement is ambiguous and the answer changes what the user sees, add it to Open Questions and ask. For purely technical choices, pick the simplest option that satisfies the NFRs and record it as a decision.

## Writing rules

- No em dashes anywhere: UI copy, logs, reports, generated files, docs. Use a colon, comma, parentheses or a full stop instead.
- Plain, direct English. UI copy is short and specific.
- Screen terms vs code terms: code uses the code terms listed in `docs/requirements.md` §Naming. Only the UI layer renames.

## Commands

```
# backend (from backend/)
uv sync                          # make backend/.venv with dev packages
uv run pytest                    # backend tests
uv run python tests/dashboard_fixtures.py   # rewrite the frontend's dashboard fixtures, both iterations, after a dashboard change (D-56, D-60)
uv run python tests/report_fixtures.py      # rewrite the frontend's report fixtures (both iterations' reports, iteration 2 rebuilt with the demo feedback; iteration 1's events) after a build, routing, validator or report change (D-64, D-67)
uv run python tests/seed_fixtures.py        # rewrite the golden Seed files (tests/golden/seed/) and the frontend's Seed page fixtures, both approval paths, after a generation, approval or report change (D-72, D-73)

# frontend (from frontend/)
npm install
npm test                         # vitest
npm run typecheck                # vue-tsc
npm run build                    # typecheck, vite build, then postbuild: no external URL in dist/ (D-38)

# all tests (from the repo root)
python run.py test

# launch both (from the repo root): app at http://127.0.0.1:5273, API at http://127.0.0.1:8100/api
python run.py
# Windows fallback where uv is blocked (pip into backend/.venv, then run.py):
powershell -ExecutionPolicy Bypass -File .\run.ps1          # launch
powershell -ExecutionPolicy Bypass -File .\run.ps1 -Dev test   # install test packages, run all tests
```

After changing backend dependencies, re-export the pip files: `uv export --no-dev --no-hashes --no-emit-project -o requirements.txt` and `uv export --no-hashes --no-emit-project -o requirements-dev.txt` (D-25).

## Definition of done for any milestone

- Exit criteria in `docs/implementation-plan.md` are met.
- Backend and frontend test suites pass. No skipped tests without a decision entry.
- Determinism test passes (from M5 onward).
- Build log entry written (`docs/project-notes.md` §Build log).
- Milestone status updated in `docs/implementation-plan.md`.
- Any doc that no longer matches the code is corrected.
