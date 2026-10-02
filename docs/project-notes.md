# SeedFoundry: Project notes

## 1. What SeedFoundry is

SeedFoundry is a lab where Seeds are formed. A person brings domain knowledge as four Ensemble files (Person, Instrument Awareness, Environment, Music) plus any extra context. SeedFoundry then:

1. **Generates** a Seed: distils the knowledge (simulated LLM), synthesises the Seed v0.1 deployment files (core, adaptation, protection), and cross-checks them.
2. **Tests** the Seed: plants it in an isolated sandbox through a simulated Seed v0.1 API, runs its full lifecycle with every human gate auto-resolved, then probes and validates the output.
3. **Refines** the Seed: shows the result (a License Optimization dashboard and a build report) to an observer, who approves or sends it back with feedback. A rebuild replays every phase with the feedback added.

The point of the demo is the improvement loop. Iteration 1 is visibly flawed and the report catches the flaws. Iteration 2, after human feedback, is clean.

## 2. Why it exists

Seed v0.1 showed what a methodology-driven analytical system looks like once it is running. It did not show where a Seed comes from or how one gets better. SeedFoundry fills that gap: knowledge in, Seed out, with testing and a human in the loop. Like Seed v0.1, it is a simulation built to communicate the idea convincingly and reliably, with seams left in place so real components could replace the simulated ones later.

## 3. The Ensemble model (short form)

Full text: `docs/ensemble/ensemble_context.md`.

| File | Question | Holds |
|---|---|---|
| `person.md` (also `player.md`) | Who performs the work? | Expertise, reasoning methods, decision patterns |
| `instrument-awareness.md` | What tool is used? | Model strengths, limits, context and token strategy |
| `environment.md` | Where does it happen? | Data, UX, Styling, Adaptation, Protection layers |
| `music.md` | Why, and how is value created? | Purpose, principles, value logic, decision logic (the IP) |

Plus **current data**, supplied at run time, never inside the four files.

SeedFoundry also accepts any number of **Misc Context** files.

## 4. From Ensemble to Seed v0.1 (internal mapping, never shown in the UI)

| Generated file | Built mainly from |
|---|---|
| `core.md` | `music.md` (all sections), with `person.md` folded in as reasoning guidance and `instrument-awareness.md` as execution guidance |
| `adaptation.md` | `environment.md` Adaptation layer, plus Data layer mappings and relevant Misc Context |
| `protection.md` | `environment.md` Protection layer, plus validation rules learned during testing |

This mapping drives generation but the UI never states it (D-9).

## 5. Glossary

| Term | Meaning |
|---|---|
| Seed | A deployable unit of Seed v0.1, described by core, adaptation and protection files |
| Intake | The knowledge files a person provides for one Seed |
| Build | One full run through all phases for one iteration |
| Iteration | Build 1 (flawed) or build 2 (refined). Exactly two exist (D-6) |
| Phase / sub-step | Major stage of a build and its smaller steps (see `build-simulation.md`) |
| Finding | A defect detected by a validator, with an id like `N-2` or `V-4` |
| Observer | The human in the loop who approves or rejects |
| Demo controller | Hidden operator panel toggled by a Shift shortcut |
| Sandbox | The simulated isolated environment where the Seed is planted |

## 6. Build log

One entry per milestone, newest last. Format in `docs/methodology.md` §4.

### M0: Read, reuse notes, scaffold (2026-10-03)

**What changed**
- Every SeedFoundry doc and every file in `docs/seed_docs/` was read. What we take from Seed v0.1 is recorded in `docs/seed-reuse-notes.md`: design tokens with values, architecture patterns, the Planting, Life and Cleanup lifecycle, the three human gates, shortcuts, process, stack.
- The Licence Utilisation dashboard is pinned down in `seed-reuse-notes.md` §5: five KPIs, a treemap, three charts, two tables, the headline figures (13,620 entitled, 13,002 assigned, 9,496 active, 3,171 unused or underused, $390k recoverable), and all 14 planted defects mapped to real panels with the rule that derives each shown value.
- Open questions: OQ-1, OQ-4, OQ-5, OQ-6 and OQ-10 closed from the Seed docs. OQ-11 to OQ-14 opened.
- Repo scaffolded: backend package tree with empty modules and a health route, frontend Vue 3 + Vite + Pinia placeholder, `run.py` launcher and `run.ps1` Windows fallback. No features.

**Files**
- NEW docs/seed-reuse-notes.md
- CHANGE docs/decisions.md (D-23 to D-25; OQ-1, 4, 5, 6, 10 closed; OQ-11 to OQ-14 opened)
- CHANGE docs/CLAUDE.md (commands; reuse notes in the file table)
- CHANGE docs/ui-spec.md (§1 dashboard route, OQ-4)
- CHANGE docs/implementation-plan.md (M0 status; as-built note on the repo layout)
- CHANGE docs/project-notes.md (this entry)
- NEW run.py, run.ps1, .gitignore, var/.gitkeep
- NEW backend/pyproject.toml, backend/uv.lock, backend/requirements.txt, backend/requirements-dev.txt
- NEW backend/seedfoundry/: `__init__.py`, main.py (health route), config.py (ports), state.py, store.py, events.py, and packages intake, engine, clients, dashboard, validators, report, generate, sample, data (docstrings only)
- NEW backend/tests/test_smoke.py
- NEW frontend/package.json, package-lock.json, vite.config.ts, tsconfig.json, index.html, src/main.ts, src/App.vue, src/env.d.ts, src/styles/tokens.css and defects.css (comment stubs), src/components, views, stores, demo (empty)
- NEW frontend/tests/smoke.spec.ts

**Gates**
- backend: 1 passed, frontend: 1 passed (both through `python run.py test`, and again through `run.ps1 -Dev test`)
- frontend typecheck and build: pass
- determinism: not yet applicable (from M5) | no-em-dash: no test yet (from M3); every file written in M0 was searched for em dashes and has none | network: the served page references no external host
- assertions edited: none

**Hand checks**
- `python run.py` started both processes and printed the ready line. `http://127.0.0.1:8100/api/health` and `http://127.0.0.1:5273/api/health` (through the Vite proxy) both answered `{"status":"ok","app":"SeedFoundry"}`. `http://127.0.0.1:5273/` served the placeholder page. These were checked over HTTP from the terminal, not in a browser window.
- Ports 8100 and 5273 were free again after stopping.

**Decisions and questions**
- New: D-23 (run.py launcher and test runner, no Makefile, Vite on 127.0.0.1), D-24 (TypeScript pinned to 6.0.x for vue-tsc), D-25 (uv project in backend/, shared `.venv`, exported requirements, httpx2)
- Opened: OQ-11 (phase catalogue against Seed's lifecycle order), OQ-12 (dashboard title), OQ-13 (defect to panel mapping), OQ-14 (dashboard interaction scope)
- Closed: OQ-1 (same stack, confirmed), OQ-4 (overlay over the report, URL-synced), OQ-5 (Shift+O and the map in reuse notes §6.2), OQ-6 (reuse notes §5), OQ-10 (three gates by id; placement waits on OQ-11)

**Notes for next milestone**
- OQ-11 decides where Planting, Seeding, Cleanup and Life sit in the catalogue. It must be answered before M5, not M1.
- `tokens.css` is not in the Seed docs. M2 rebuilds it from `seed-reuse-notes.md` §1.3 and picks the missing values (shadows, easing, chart grid, scrollbar).
- The Seed docs have the dashboard's headline figures but no rows. M7 has to write a generator that reproduces them exactly, plus an alternate dataset for the data-swap test.
- `docs/ensemble_context.md` is a byte-identical copy of `docs/ensemble/ensemble_context.md` and is not in the doc index. Left in place pending a ruling.
- No git commit was made in M0.

### M0 follow-up: open questions answered (2026-10-03)

**What changed**
- OQ-11: eleven phases kept (read as option A). Phase 8 is now **Seeding & Life**, running Seed v0.1's Discovery, Assessment, Implementation, Cleanup and Life in Seed's order, with the three gates resolved inside it. Phase 11 is now **Teardown & Report**. Count, order, weights and test ids are unchanged.
- OQ-12: the dashboard is titled **License Optimization**.
- OQ-13: the defect-to-panel mapping in `seed-reuse-notes.md` §5.8 is confirmed; no panels are added.
- OQ-14: the dashboard supports **drill-down** in both iterations: Seed v0.1's hierarchy down to seats, every panel following the drill, breadcrumb and Back, drill path in the URL. This widens M7.

**Files**
- CHANGE docs/decisions.md (D-26 to D-29; OQ-11 to OQ-14 closed; OQ-15 opened; R-9 added)
- CHANGE docs/requirements.md (A-1 amends FR-B-5; A-2 adds FR-D-6; new §10 Amendments)
- CHANGE docs/build-simulation.md (§2 phases 7, 8 and 11 and the results table; §4 example lines use the real gate id, panel name and figures; §5 points to the confirmed mapping)
- CHANGE docs/ui-spec.md (§1 route carries `drill`; §5 title and drill-down)
- CHANGE docs/implementation-plan.md (M5 gate wording; M7 and M8 scope and exit for drill-down)
- CHANGE docs/seed-reuse-notes.md (§3.3, §4.2, §5.1, §5.3, §5.6, §5.8 and §10 brought to the rulings)

**Gates**
- No code changed. backend: 1 passed, frontend: 1 passed (unchanged from M0)
- assertions edited: none

**Decisions and questions**
- New: D-26 (catalogue in Seed's order), D-27 (title), D-28 (defect mapping), D-29 (drill-down)
- Opened: OQ-15 (evidence panel, assumed no)
- Closed: OQ-11, OQ-12, OQ-13, OQ-14 (stakeholder)

**Notes for next milestone**
- M7 now carries a filter context, a query engine over seat rows, and URL-synced drill state, on top of the data generator. The proposal to split M7 is still open.
- Still open for the stakeholder: OQ-2, OQ-3, OQ-7, OQ-8, OQ-9, OQ-15.
- Later the same day (D-30, A-3): the dashboard's underlying data need not match Seed v0.1; the methodology and the layout must. `seed-reuse-notes.md` §5.5 is now reference only and §5.7 lists what the data must follow and the constraints the tests need. M7's generator no longer reproduces Seed's figures. CHANGE: decisions.md, requirements.md (FR-D-1), implementation-plan.md (M7), build-simulation.md (§4 example figures), seed-reuse-notes.md (§5).
- Then: the stakeholder accepted every remaining assumption. OQ-2, OQ-3, OQ-7, OQ-8, OQ-9 and OQ-15 are closed as assumed. No open question remains. CHANGE: decisions.md.
