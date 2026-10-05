# SeedFactory: Implementation plan

Status values: Not started, In progress, Done, Blocked. Update the table and add a build log entry at the end of every milestone.

## 1. Milestones at a glance

| Phase | Milestone | Title | Status | Commit |
|---|---|---|---|---|
| A. Foundations | M0 | Read, reuse notes, scaffold | Done (2026-10-03) | `ec42517` |
| | M1 | Backend core: state, persistence, events, SSE | Done (2026-10-03) | `de1b8e1` (D-36's docs: `0503049`) |
| | M2 | Frontend shell and design system | Done (2026-10-03) | `6b7cc90` |
| B. Knowledge | M3 | Intake page | Done (2026-10-03) | `63de277` |
| | M4 | Demo controller and sample Seed | Done (2026-10-03) | `8468cdc` |
| C. Build | M5 | Beat engine, phase catalogue, simulated clients | Done (2026-10-03) | `3657602` |
| | M6 | Build page: stepper and console | Done (2026-10-03) | `7eece3f` |
| D. Output | M7 | Polished License Optimization dashboard | Done (2026-10-03) | `51c8f7c` |
| | M8 | Defect overlay (iteration 1 dashboard) | Done (2026-10-03) | `5543754` |
| | M9 | Validators and build report | Done (2026-10-04) | `6169080` |
| E. Loop | M10 | Rebuild modal and iteration 2 | Done (2026-10-04) | `7dd8136` |
| | M11 | Seed file generation and final page | Done (2026-10-04) | `37155f5` |
| F. Ship | M12 | Hardening, operator guide, rehearsal | Done (2026-10-04) | `351a1c7` |
| | M13 | As-built reconciliation | Done (2026-10-04) | "M13: as-built reconciliation", the commit after `351a1c7` |
| G. Feedback | CR-1 | Stakeholder feedback after M13: open-ended iterations, Reject everywhere, context footprint, feedback routing panel | Done (2026-10-04) | the commit after `a50bd81` |
| | CR-2 | Demo feedback: SeedFactory, initiation files and versioned names, Human tag, console note, View Agentic Solution, QUAD SI, Secure and Lock | Done (2026-10-05) | the commit after `b363cd3` |

*As built (M13):* the Commit column was added in M13, as Seed v0.1's status table had one (`seed-reuse-notes.md` §7).

Critical path: M0 → M1 → M5 → M7 → M8 → M9 → M10 → M11 → M12. M2, M3, M4 and M6 can proceed in parallel with the backend chain once M1 lands.

## 2. Repo layout (target)

```
seedfoundry/
  CLAUDE.md                  # one line: @docs/CLAUDE.md (so Claude Code auto-loads the rules)
  run.ps1                    # Windows launcher (uv blocked fallback)
  Makefile or justfile       # launch, test, lint
  backend/
    pyproject.toml
    seedfoundry/
      main.py                # FastAPI app, routes
      state.py               # single source of truth, snapshot
      store.py               # JSON persistence under var/
      events.py              # event log, SSE, snapshot-then-replay
      intake/                # files, categories, assay, boundary lint
      engine/                # beat engine, phases, clock, weights
      clients/               # LLMClient, SeedClient + simulated impls
      dashboard/             # data, descriptor, defect overlay
      validators/            # numeric, visual, latency, boundary
      report/                # report assembly
      generate/              # core/adaptation/protection templates, zip
      sample/                # sample Seed markdown files
      data/                  # License Optimization datasets (primary + alternate)
    tests/
  frontend/
    package.json
    src/
      styles/tokens.css      # from Seed v0.1
      styles/defects.css     # scoped, iteration 1 dashboard only
      components/            # Editor, FilePanel, Stepper, Console, Report, Dashboard panels, Modal
      views/                 # Knowledge, Build, Review, Dashboard, Seed
      stores/
      demo/                  # demo controller
    tests/
  docs/                      # all project docs, incl. CLAUDE.md and KICKOFF_PROMPT.md
  var/                       # runtime data (gitignored)
```

*As built (M0):* the repository root is the `seedfoundry/` folder above, so there is no extra wrapper directory. There is no Makefile or justfile: `run.py` launches both processes and `run.py test` runs both suites (D-23). Also at the root: `.gitignore`. In `backend/`: `uv.lock`, `requirements.txt` and `requirements-dev.txt` (D-25), and `seedfoundry/config.py` holding the two ports. In `frontend/`: `index.html`, `vite.config.ts`, `tsconfig.json`, `src/main.ts`, `src/App.vue` ~~(placeholder)~~ (the shell since M2, D-39), `src/env.d.ts`.

*As built (M1):* intake rules live in `backend/seedfoundry/intake/files.py`. `config.py` also gives `var_dir()`, which `SEEDFOUNDRY_VAR_DIR` overrides (tests use it). `main.py` builds the app with `create_app()`, which loads the state when the app starts. `backend/tests/conftest.py` can start a real uvicorn process over a temporary `var/` for restart and SSE tests.

*As built (M2):* `frontend/src/` also holds `router.ts`, `theme.ts`, `events.ts` (event types the client listens for), `stores/lab.ts` (live state), `styles/base.css`, `components/base/` (button, chip, card, modal, tooltip), `components/shell/` (top bar, journey indicator, iteration badge, theme toggle) and `components/ScreenPlaceholder.vue`. Views are `KnowledgeView`, `BuildView`, `ReviewView`, `SeedView`; the dashboard is an overlay on the review route, so it will be a component, not a view (OQ-4). `frontend/scripts/check-network.ts` runs as `postbuild` (D-38).

*As built (M3):* `frontend/src/` also holds `api.ts` (JSON over `/api`, server errors as `ApiError`), `intake.ts` (intake API calls, types, shared rules), `markdown.ts` (Preview rendering and sanitising, D-40), `stores/intake.ts` (categories, drafts, autosave, file actions, D-41), `components/base/BaseMenu.vue` and `BaseConfirm.vue`, and `components/intake/` (FileEditor, FilePanel, MarkdownPreview, NewFileDialog, ImportDialog, EmptyState). There is no separate Editor component directory: the editor is `components/intake/FileEditor.vue`, which M10's rebuild modal can reuse. `frontend/tests/` holds `fake-server.ts` (an in-memory intake API for page tests) and `fixtures/` (four core files, one Misc Context file, and the hostile sample). The no em dash test is `backend/tests/test_no_em_dash.py` (D-44).

*As built (M4):* `backend/seedfoundry/demo.py` holds the demo controller's server actions (Load sample Seed, Clear intake, Reset to start, D-46), under `/api/demo/`. `backend/seedfoundry/sample/` holds the five sample files and `sample_files()`. `frontend/src/demo/` holds `DemoController.vue` (the panel, mounted in `App.vue`), `shortcuts.ts` (the map and the ignore rules, D-47) and `api.ts`; its store is `frontend/src/stores/demo.ts`, beside the others. Start Build's M3 action moved from `KnowledgeView.vue` into `stores/intake.ts` (`startBuild`, `buildNote`) so Shift+Enter shares it.

*As built (M5):* `backend/seedfoundry/engine/` holds `catalogue.py`, `script.py`, `runner.py` and `clock.py` (D-48). `clients/` holds `llm.py` and `seed.py` (D-22). `intake/` gained `assay.py` (inventory, coverage, statements, Seed name, fingerprint), `boundary.py` (D-50) and `feedback.py` (the feedback file and its segments). ~~`generate/outline.py` drafts the layer outlines and the manifest until M11 (D-51). `validators/` is still empty: the stubbed tests are in `engine/script.py` until M9.~~ (superseded: `validators/` from M7, `generate/layers.py` in M11) Builds are `POST /api/builds` and `GET /api/builds/{id}/events`; speed and skip are `GET`/`POST /api/demo/speed` and `POST /api/demo/skip` (D-49). Frontend: `src/builds.ts` (build API); `events.ts` exports `BUILD_EVENT_TYPES`; the lab store reduces build events (D-53). New tests: `backend/tests/test_assay.py`, `test_boundary.py`, `test_engine.py`, `test_build_api.py`; `frontend/tests/build-view.spec.ts`.

*As built (M6):* the Build page is `frontend/src/views/BuildView.vue` with `components/build/` (`PhaseStepper.vue`, `BuildConsole.vue`, `BuildSummary.vue`), so the plan's Stepper and Console components live there. `src/stepper.ts` derives phases, sub-steps, times and console lines from events (pure functions). `src/stores/buildLog.ts` holds the shown build's events (D-54). The lab store gained `onEvent` and `refreshes`. `builds.ts` gained `buildsApi.events`. The build record gained `sim_seconds` (`state.py`, set in `engine/script.py`). New tests: `frontend/tests/stepper.spec.ts`, and `build-view.spec.ts` rewritten for the page, with `tests/build-script.ts` generating a build's events.

*As built (M7):* `backend/seedfoundry/data/` holds `model.py` (the seat record and methodology), `estates.py` (the primary and alternate estate specs) and `generate.py` (the seeded generator, D-55). `dashboard/` holds `descriptor.py`, `query.py` (the drill path and aggregations) and `payload.py` (D-56)~~; there is no separate defect overlay file until M8~~ (`overlay.py` since M8). `validators/` holds `numeric.py`, `visual.py`, `structure.py`, `tokens.py` and `problems.py` (D-57, D-58). Routes: `GET /api/dashboards/license-optimization` (and `/descriptor`), `GET /api/datasets`, `GET /api/datasets/{name}`. Frontend: `src/dashboard/` (types, API, drill path, formats, tokens, ECharts setup and options) and `components/dashboard/` (`DashboardFrame`, `DashboardView`, `DashboardRenderer`, `DrillBar`, `KpiPanel`, `ChartPanel`, `TablePanel`), so the dashboard is a component, not a view: `views/ReviewView.vue` shows the frame over the review route (D-59). New tests: `backend/tests/test_data.py`, `test_dashboard.py`, `test_validators.py`, with `dashboard_fixtures.py` writing `frontend/tests/fixtures/dashboard/`; `frontend/tests/dashboard.spec.ts`, `dashboard-units.spec.ts`, `fake-echarts.ts`.

*As built (M8):* `backend/seedfoundry/dashboard/overlay.py` holds the defect overlay (D-60): fourteen patches in descriptor, payload and styles layers; `descriptor(1)` and `build()` apply it, and `GET /api/dashboards/license-optimization/overlay` serves it. `validators/` gained `styles.py` (reads the stylesheet a descriptor names) and `latency.py` (T-15). Frontend: `src/styles/defects.css` (scoped under `.defects-overlay`), `src/dashboard/stylesheets.ts` (loads a descriptor's named sheet on demand) and `src/dashboard/latency.ts` (a panel's declared wait). The dashboard fixtures are now `frontend/tests/fixtures/dashboard/iteration-1/` and `iteration-2/`. New tests: `backend/tests/test_overlay.py`.

*As built (M9):* `backend/seedfoundry/validators/` gained `findings.py` (problems to findings, D-63), `protection.py` (T-13) and `records.py` (T-14) (D-62); `report/assemble.py` assembles the report from a build's kept log (D-64), served at `GET /api/builds/{id}/report`. The validators run in `engine/script.py`, and `pending(...)` is gone. Frontend: `src/report.ts` (types, API), `src/stores/reports.ts` (one load per build), `components/report/BuildReport.vue` (the report, on the Build and Review pages, D-65); `components/build/BuildSummary.vue` is removed. The dashboard frame has the "N findings" link and the finding highlight (`finding=<id>`), drawn by `DashboardRenderer.vue`. New tests: `backend/tests/test_findings.py`, `test_probes.py`, `test_report.py`, with `report_fixtures.py` writing `frontend/tests/fixtures/reports/`; `frontend/tests/report.spec.ts`.

*As built (M10):* `backend/seedfoundry/intake/routing.py` routes the observer feedback into the four core files (D-68); `engine/script.py`'s Apply observer feedback sub-steps use it and `engine/runner.py` writes each routed file as its beat plays and saves the rebuild's feedback with the build's start (D-67); the build record keeps `files` (`GET /api/builds/{id}/files`); `report/assemble.py` adds `changes` to iteration 2's report (D-69); `GET /api/demo/feedback` serves `sample/rebuild/observer-feedback-iteration-1.md`. Frontend: `components/rebuild/RebuildModal.vue` and `stores/rebuild.ts` (D-70), `components/intake/MarkdownEditor.vue` (the editor FileEditor and the modal share), and `BaseModal` gained `name`, a `controls` slot and a `flush` body. New tests: `backend/tests/test_routing.py`, `test_rebuild.py`; `frontend/tests/rebuild-modal.spec.ts`.

*As built (M11):* `backend/seedfoundry/generate/` holds `layers.py` (the three files' templates, the manifest; the M5 `outline.py` renamed, D-72); the zip, Approve and the Seed page's data are `backend/seedfoundry/package.py` (D-73, D-74), served at `POST /api/seed/approve`, `GET /api/seed`, `GET /api/seed/files/{name}` and `GET /api/seed/zip`. `state.py`'s `Approval` gained `build_id` and `approved_at`; `events.py` gained `seed.approved`. Frontend: `src/seed.ts` (types, API), `stores/seed.ts`, `views/SeedView.vue` and `components/seed/` (`SeedHistory.vue`, `SeedFiles.vue`); `BuildReport.vue`'s Approve is real and the journey indicator links Seed once approved (D-75). `components/ScreenPlaceholder.vue` is removed: `/seed` was the last screen using it. New tests: `backend/tests/test_seed.py`, with `seed_fixtures.py` writing the golden files (`backend/tests/golden/seed/`) and `frontend/tests/fixtures/seed/`; `frontend/tests/seed.spec.ts`.

*As built (M12, D-77):* `docs/operator-guide.md` is the operator guide. `frontend/scripts/rehearse.ts` (`npm run rehearse`) is the rehearsal: the whole demo in headless Chrome against an isolated copy of the app, offline, with screenshots and `results.json`. `backend/tests/offline.py` is the offline guard, `backend/tests/offline_guard/sitecustomize.py` loads it into a server process, and `backend/tests/test_offline.py` runs the demo under it. `frontend/vite.config.ts` reads `SEEDFOUNDRY_API_URL` for its proxy target (the rehearsal's copy; `run.py` leaves the default).

*As built (M13, D-78, D-79):* `backend/tests/test_launcher.py` tests `run.py`'s job object. `docs/ensemble_context.md`, a duplicate, is removed.

*As built (summary, M13):* the repository as it is at M13, top levels, with what each folder holds. Files listed by name where a folder's purpose is the file.

```
SeedFoundry/                       # the repository root (the folder keeps its first name, D-87); no wrapper folder
  CLAUDE.md                        # one line: @docs/CLAUDE.md
  run.py                           # launch both processes, or `run.py test` for both suites (D-23, D-78)
  run.ps1                          # Windows, where uv is blocked: pip into backend/.venv, then run.py (D-25)
  .gitignore
  backend/                         # Python 3.12+, FastAPI under uvicorn; a uv project
    pyproject.toml  uv.lock        # dependencies; the lock is the source of truth (D-25)
    requirements.txt  requirements-dev.txt   # exported from the lock, for pip
    seedfoundry/
      main.py                      # create_app(): every /api route
      config.py                    # ports 8100 and 5273, var_dir()
      state.py                     # the state model; every change on a copy, saved, then published (D-32)
      store.py                     # JSON under var/, written atomically (D-3)
      events.py                    # event types, the event log, SSE with snapshot then replay (D-31)
      demo.py                      # Load sample, Clear, Reset, as state changes (D-46)
      package.py                   # Approve, Known issues, the Seed page's data, downloads, the zip (D-73, D-74)
      intake/                      # files and categories, Assay, boundary lint, feedback segments, routing
      engine/                      # the beat engine: catalogue, script, runner, clock (D-48)
      clients/                     # LLMClient and SeedClient, simulated only (D-22)
      data/                        # the seat record, two estates, the seeded generator (D-55)
      dashboard/                   # descriptor, query engine, payload, the defect overlay (D-56, D-60)
      validators/                  # numeric, visual, styles, tokens, structure, latency, protection, records, findings
      report/                      # the report, assembled from a build's kept log (D-64, D-69)
      generate/                    # the three Seed files' templates, layers.py (D-72)
      sample/                      # the sample Seed's five files; rebuild/ holds the demo feedback (iteration 1's, and later's, D-81)
    tests/                         # pytest, one file per area; offline.py (the guard); the fixture writers
      golden/seed/                 # the Seed files for both approval paths
      offline_guard/               # sitecustomize.py: the guard inside a server process (D-77)
  frontend/                        # Vue 3, TypeScript, Pinia, Vite, ECharts; vitest
    package.json  package-lock.json  tsconfig.json  vite.config.ts  index.html
    scripts/                       # check-network.ts (postbuild, D-38), rehearse.ts (npm run rehearse, D-77)
    src/
      main.ts  App.vue  router.ts  theme.ts  api.ts  events.ts   # start-up, shell, routes, theme, API and event types
      intake.ts  builds.ts  report.ts  seed.ts  markdown.ts  stepper.ts   # each area's API calls, types and pure helpers
      styles/                      # tokens.css (Seed v0.1's values, D-37), base.css, defects.css (iteration 1 only)
      components/                  # base/, shell/, intake/, build/, report/, dashboard/, rebuild/, seed/
      views/                       # KnowledgeView, BuildView, ReviewView, SeedView
      dashboard/                   # types, API, drill path, formats, tokens, ECharts set-up and options, latency, stylesheets
      stores/                      # lab (live state), intake, buildLog, reports, rebuild, seed, demo
      demo/                        # DemoController.vue, shortcuts.ts, api.ts
    tests/                         # vitest specs; fake-server.ts, fake-echarts.ts, build-script.ts, helpers.ts
      fixtures/                    # sample and hostile files; dashboard/, reports/, seed/ written by the backend's scripts
  docs/                            # every project doc; ensemble/ the Ensemble text; seed_docs/ Seed v0.1's, read only
  var/                             # runtime data, state.json (gitignored, but for .gitkeep)
```

Fonts are the `@fontsource-variable` packages, imported in `main.ts` and bundled. Not in git: `backend/.venv`, `frontend/node_modules`, `frontend/dist` and `var/state.json`.

## 3. Milestones

Each milestone lists scope, exit criteria and hand checks. Tag changes in the build log as NEW, CHANGE or MOVE.

### M0: Read, reuse notes, scaffold
- **Scope:** read all docs and `seed_docs/`; write `seed-reuse-notes.md` (reuse items, dashboard spec, lifecycle steps for Planting/Life/Cleanup, human gate list, shortcuts, tokens, contradictions); close what OQs the seed docs can settle; scaffold repo, toolchain, smoke tests; fill the commands section of docs/CLAUDE.md.
- **Exit:** reuse notes complete incl. §Dashboard with panels mapped to defects N-1..L-1; OQ-4, 5, 6, 10 closed or explained; both smoke tests pass; launch command starts both processes.
- **Hand check:** open both URLs; nothing but a placeholder.

### M1: Backend core
- **Scope:** state model (intake, builds, iterations, approval), JSON store with atomic writes, event log, SSE endpoint with snapshot-then-replay, intake CRUD API, import API with category handling and one-per-core rule.
- **Exit:** API tests for CRUD, replace rule, persistence across restart, SSE replay order.
- **Hand check:** create a file via API, restart server, file is still there.

### M2: Frontend shell and design system
- **Scope:** port tokens.css, bundled fonts, light/dark, app shell with journey indicator and routes, base components (button, chip, card, modal, tooltip), contrast test.
- **Exit:** contrast test passes in both themes; routes render placeholders; no network requests outside localhost.
- **Hand check:** theme toggle; visual match to Seed v0.1 tokens.

### M3: Intake page
- **Scope:** editor with Edit/Preview (sanitised render), mic icon, name and category, file panel grouped by category, new/rename/delete, autosave and unsaved dot, import with category dialog and filename pre-selection, core checklist, Start Build gating, empty state, size and encoding errors.
- **Exit:** FR-IN-1..11 covered by tests; hostile markdown sample renders safely.
- **Hand check:** import the four files, see checklist complete, refresh, still there.

### M4: Demo controller and sample Seed
- **Scope:** controller panel, Shift shortcut ignored in text fields, actions wired (build actions stubbed until M5/M6), sample Seed files per `build-simulation.md` §8, Ensemble-clean.
- **Exit:** Load sample Seed fills intake; shortcut test incl. text-field case.
- **Hand check:** read the four sample files; they read like a real Ensemble bundle.

### M5: Beat engine, phases, simulated clients
- **Scope:** generator engine, weights and simulated clock, speed and skip, all 11 phases with sub-steps and log lines (iteration 1 and 2 scripts), `LLMClient`/`SeedClient` simulated implementations, Assay stats and boundary lint (real), ~~auto-resolved Life gates~~ the three Seed v0.1 gates auto-resolved in phase 8 (D-26), events per `build-simulation.md` §3. Validators stubbed.
- **Exit:** determinism test (two runs, identical streams ignoring `wall_ts`); build length 60 to 90 s at 1x in a clock test; boundary lint tests incl. zero findings on sample.
- **Hand check:** watch the event stream in the terminal; reads sensibly.

### M6: Build page
- **Scope:** stepper with states and sub-steps, console with levels, filter, pause, progress and elapsed, reconnect on refresh, transition to report panel on completion.
- **Exit:** refresh mid-build resumes with full log (test); FR-B-1..9.
- **Hand check:** run a build at 1x end to end; nothing jumps or flickers.

### M7: Polished dashboard
- **Scope:** License Optimization data (primary and alternate for data-swap), descriptor, all panels as in reuse notes, polished per Seed v0.1, "Back to report" frame. *Added by D-29 and D-30:* ~~a data generator that reproduces the headline figures in `seed-reuse-notes.md` §5.5 exactly~~ a seeded data generator for SeedFactory's own estate that follows the methodology and meets the constraints in `seed-reuse-notes.md` §5.7; the drill hierarchy as data; one filter context and a query engine that aggregates from seat rows; drill bar with breadcrumb and Back; drill path in the URL; the Seats table paginated at the deepest level.
- **Exit:** numeric reconciliation on polished payload passes; visual QA rules pass (validators can be minimal here and completed in M9). *Added by D-29:* query engine matches row-level ground truth at every hierarchy level (test); reload keeps the drill path; browser Back pops one step.
- **Hand check:** side by side with Seed v0.1 screenshots or descriptions; reads as the same dashboard. Drill from the treemap to one product's Unused seats and back.

### M8: Defect overlay
- **Scope:** descriptor patches and scoped `defects.css` implementing N-1..N-5, V-1..V-8, L-1, figures derived from data.
- **Exit:** overlay applies only to iteration 1 dashboard (test); SeedFactory UI contrast test still passes. *Added by D-29:* the overlay stays applied at a sample of drill levels (test, R-9).
- **Hand check:** a first-time viewer would call it unfinished within five seconds.

### M9: Validators and report
- **Scope:** numeric, visual, latency validators complete; findings model; report assembly and report UI (findings grouped, tests table, gates, simulated usage), finding to dashboard panel highlight.
- **Exit:** D-14 test (sample iteration 1 findings equal catalogue exactly; polished has zero).
- **Hand check:** every finding in the report is visible on the dashboard where it says.

### M10: Rebuild and iteration 2
- **Scope:** rebuild modal with editor and split views, feedback saved as Misc Context, iteration 2 run with its script, "Changes since iteration 1", Rebuild hidden on iteration 2, demo controller prefill. *Added by D-36:* feedback routing into the four core files (segmenting, boundary-rule scoring, verbatim append under `### Observer feedback (iteration 1)`), iteration 1 file versions kept with build 1, the "Apply observer feedback" sub-steps and log lines in phase 1 of iteration 2, and prefill text that reaches all four files.
- **Exit:** full two-iteration flow test (API level); FR-RB-1..~~6~~8, FR-R-3. *Added by D-36:* routing tests (each rule set sends a segment to the right file and section; ties break in the fixed order; an unmatched segment changes no file; same feedback gives the same edits); the prefilled feedback updates all four files and raises no boundary advisory; the log lines match the edits actually made.
- **Hand check:** write feedback while viewing the dashboard in split view; rebuild; watch phase 1 route the feedback and update the files at 1x; open Knowledge and read the added sections; iteration 2 dashboard is clean.

### M11: Generation and final page
- **Scope:** core/adaptation/protection templates, learned rules in iteration 2, known issues on iteration 1 approval, zip, final page per `ui-spec.md` §7.
- **Exit:** generated files golden tests for both approval paths; no em dash test passes over all generated output.
- **Hand check:** open the three downloaded files; they read as a coherent Seed.

### M12: Hardening and operator guide
- **Scope:** offline test (network disabled), performance checks (NFR-3), keyboard reachability, `docs/operator-guide.md` with launch, shortcuts, timed demo script (target 8 to 10 minutes), pre-demo checklist, troubleshooting; rehearsal pass at 1x.
- **Exit:** AC-1..AC-10 all verified and recorded in the build log.
- **Hand check:** full rehearsal with the demo script, timed.

### M13: As-built reconciliation
- **Scope:** update every doc to match the code (As built notes), close remaining OQs, final build log entry.
- **Exit:** no doc contradicts the code.

### CR-1: Stakeholder feedback after M13
- **Scope:** no iteration total on screen (D-80); Reject (Rebuild renamed) and Approve on every report, and iteration n + 1 from a rejected iteration n, iteration 3 on replaying iteration 2's outcome (D-81, A-7); the Seed files' context footprint in the report against a 20% budget (D-82, A-8); a Build page panel showing the feedback going into the four files (D-83).
- **Exit:** both suites and the rehearsal pass; iterations 1 and 2 give the same files and reports as at M13; the docs say what the code does.

### CR-2: Demo feedback
- **Scope:** rename to SeedFactory in visible text and docs (D-87); the four initiation files only, renamed Identity.md, Tools_and_Skills.md, Environment.md and Value.md everywhere, with no Misc Context on screen and no vendor notes in the sample (D-84); files named by their category on add and versioned by each iteration that changes them (D-85); the Seed file beside each initiation file (D-86); the console's language note (D-89); the Human tag (D-90); View Agentic Solution (D-91); Initiate QUAD SI Review Protocol (D-92); Secure and Lock in Secure Repository with a download link (D-93); the footprint note's wording (D-94).
- **Exit:** both suites, `npm run build` and the rehearsal pass; the docs say what the code does.

## 4. Safety gates (every milestone)

- No existing test assertion edited without a decision entry (docs/CLAUDE.md rule 5).
- Determinism test green from M5 on.
- No em dash test green from M3 on.
- No network calls outside localhost (checked in M2 and M12, cheap to keep running).
