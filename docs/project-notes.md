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

### M1: Backend core (2026-10-03)

**What changed**
- Knowledge files now live on the server and survive a restart. The API can create, read, rename, recategorise, rewrite and delete them, and import a `.md` file with its category picked from the filename (FR-IN-7).
- One file each for Person, Instrument Awareness, Environment and Music: a second one, whether by create, import or a category change, is refused with a "Replace it?" message naming the current file, and goes through only when the request asks to replace (FR-IN-3). Misc Context is unlimited.
- Files over 1 MB, or that are not UTF-8 text, are refused with a message the UI can show as written (FR-IN-11). Intake is read-only while a build runs (FR-B-8).
- One state object on the server holds intake, builds, the current iteration and approval. It is saved atomically to `var/state.json` before any client hears about a change.
- Every change emits events in the `build-simulation.md` §3 shape. `GET /api/state` gives the snapshot and its seq; `GET /api/events` replays from that seq over SSE, then follows. A reconnect with `Last-Event-ID` replays exactly, and a client whose history was lost in a restart is told to fetch a new snapshot.
- Two guard tests: no URL in the code names another host, and no model or LLM library is a dependency.

**Files**
- CHANGE backend/seedfoundry/store.py (atomic JSON store)
- CHANGE backend/seedfoundry/state.py (state model, categories, StateManager)
- CHANGE backend/seedfoundry/events.py (event model and types, in-memory log, SSE stream)
- CHANGE backend/seedfoundry/main.py (`create_app()`, state, events and intake routes)
- CHANGE backend/seedfoundry/config.py (`var_dir()`)
- NEW backend/seedfoundry/intake/files.py (intake rules and changes)
- NEW backend/tests/conftest.py, test_intake_api.py, test_persistence.py, test_events.py, test_guards.py
- CHANGE run.py (uvicorn graceful shutdown timeout, D-31)
- CHANGE .gitignore (`.codegraph/`, the local code index, before the M0 commit)
- CHANGE docs/decisions.md (D-31 to D-35)
- CHANGE docs/build-simulation.md (§3 as-built note on the M1 event types)
- CHANGE docs/implementation-plan.md (M1 status; as-built note)
- CHANGE docs/project-notes.md (this entry)

**Gates**
- backend: 86 passed, frontend: 1 passed (through `python run.py test`); frontend typecheck: pass
- determinism: not yet applicable (from M5); file ids and seqs come from saved counters | no-em-dash: no test yet (from M3); every file written in M1 was searched and has none | network: guard test passes
- assertions edited: none

**Hand checks**
- Started the backend as `run.py` does (port 8100, the real `var/`), created `hand-check.md` through the API, stopped the process, started it again: `GET /api/intake/files` returned the file unchanged. `GET /api/events` with `Last-Event-ID: 0` then sent a `stream.resync`, as designed, because the log before the restart was not kept. The hand-check file was then removed so `var/` starts empty. Checked over HTTP from the terminal, not in a browser; there is no UI in M1.
- The same check runs as a test (`test_file_survives_a_real_server_restart`) against a real uvicorn process, killed hard between the two starts.
- `python run.py` launched both processes; a file created through `http://127.0.0.1:5273/api` (the Vite proxy) arrived at once on `GET /api/events` through the same proxy, so SSE is not buffered. Ports 8100 and 5273 were free after stopping, and `var/` was emptied again.

**Decisions and questions**
- New: D-31 (in-memory event log, saved seq, resync), D-32 (transactional changes, intake events carry no content, counter ids), D-33 (running builds marked interrupted on restart), D-34 (FR-IN-11 at the API, raw-body import), D-35 (intake API shape, replace rule on category change, names need not be unique)
- Opened: none. Closed: none.

**Notes for next milestone**
- M3 should fetch file content with `GET /api/intake/files/{id}` after an `intake.file_updated` event whose `changed` includes `content`: events carry no content (D-32). Category labels and the filename hints come from `GET /api/intake/categories`, so the frontend needs no copy of them.
- Import is one request per file, with the file's raw bytes as the body. The import dialog can show the "Replaces existing" warning from the snapshot, and a 409 `core_slot_taken` is the server's answer if it is skipped.
- Duplicate file names are allowed (D-35). If the stakeholder wants unique names, M3 is the place to raise it.
- The frontend has no event type list yet. When M2 or M6 adds one, add Seed v0.1's contract test: the backend's `EVENT_TYPES` must all be known to the frontend.
- M1 is committed on `master` (the M0 scaffold first, as its own commit).
