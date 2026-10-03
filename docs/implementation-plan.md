# SeedFoundry: Implementation plan

Status values: Not started, In progress, Done, Blocked. Update the table and add a build log entry at the end of every milestone.

## 1. Milestones at a glance

| Phase | Milestone | Title | Status |
|---|---|---|---|
| A. Foundations | M0 | Read, reuse notes, scaffold | Done (2026-10-03) |
| | M1 | Backend core: state, persistence, events, SSE | Done (2026-10-03) |
| | M2 | Frontend shell and design system | Done (2026-10-03) |
| B. Knowledge | M3 | Intake page | Not started |
| | M4 | Demo controller and sample Seed | Not started |
| C. Build | M5 | Beat engine, phase catalogue, simulated clients | Not started |
| | M6 | Build page: stepper and console | Not started |
| D. Output | M7 | Polished License Optimization dashboard | Not started |
| | M8 | Defect overlay (iteration 1 dashboard) | Not started |
| | M9 | Validators and build report | Not started |
| E. Loop | M10 | Rebuild modal and iteration 2 | Not started |
| | M11 | Seed file generation and final page | Not started |
| F. Ship | M12 | Hardening, operator guide, rehearsal | Not started |
| | M13 | As-built reconciliation | Not started |

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

*As built (M0):* the repository root is the `seedfoundry/` folder above, so there is no extra wrapper directory. There is no Makefile or justfile: `run.py` launches both processes and `run.py test` runs both suites (D-23). Also at the root: `.gitignore`. In `backend/`: `uv.lock`, `requirements.txt` and `requirements-dev.txt` (D-25), and `seedfoundry/config.py` holding the two ports. In `frontend/`: `index.html`, `vite.config.ts`, `tsconfig.json`, `src/main.ts`, `src/App.vue` (placeholder), `src/env.d.ts`.

*As built (M1):* intake rules live in `backend/seedfoundry/intake/files.py`. `config.py` also gives `var_dir()`, which `SEEDFOUNDRY_VAR_DIR` overrides (tests use it). `main.py` builds the app with `create_app()`, which loads the state when the app starts. `backend/tests/conftest.py` can start a real uvicorn process over a temporary `var/` for restart and SSE tests.

*As built (M2):* `frontend/src/` also holds `router.ts`, `theme.ts`, `events.ts` (event types the client listens for), `stores/lab.ts` (live state), `styles/base.css`, `components/base/` (button, chip, card, modal, tooltip), `components/shell/` (top bar, journey indicator, iteration badge, theme toggle) and `components/ScreenPlaceholder.vue`. Views are `KnowledgeView`, `BuildView`, `ReviewView`, `SeedView`; the dashboard is an overlay on the review route, so it will be a component, not a view (OQ-4). `frontend/scripts/check-network.ts` runs as `postbuild` (D-38).

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
- **Scope:** License Optimization data (primary and alternate for data-swap), descriptor, all panels as in reuse notes, polished per Seed v0.1, "Back to report" frame. *Added by D-29 and D-30:* ~~a data generator that reproduces the headline figures in `seed-reuse-notes.md` §5.5 exactly~~ a seeded data generator for SeedFoundry's own estate that follows the methodology and meets the constraints in `seed-reuse-notes.md` §5.7; the drill hierarchy as data; one filter context and a query engine that aggregates from seat rows; drill bar with breadcrumb and Back; drill path in the URL; the Seats table paginated at the deepest level.
- **Exit:** numeric reconciliation on polished payload passes; visual QA rules pass (validators can be minimal here and completed in M9). *Added by D-29:* query engine matches row-level ground truth at every hierarchy level (test); reload keeps the drill path; browser Back pops one step.
- **Hand check:** side by side with Seed v0.1 screenshots or descriptions; reads as the same dashboard. Drill from the treemap to one product's Unused seats and back.

### M8: Defect overlay
- **Scope:** descriptor patches and scoped `defects.css` implementing N-1..N-5, V-1..V-8, L-1, figures derived from data.
- **Exit:** overlay applies only to iteration 1 dashboard (test); SeedFoundry UI contrast test still passes. *Added by D-29:* the overlay stays applied at a sample of drill levels (test, R-9).
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

## 4. Safety gates (every milestone)

- No existing test assertion edited without a decision entry (docs/CLAUDE.md rule 5).
- Determinism test green from M5 on.
- No em dash test green from M3 on.
- No network calls outside localhost (checked in M2 and M12, cheap to keep running).
