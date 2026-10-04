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

### Change request: feedback updates the four files (2026-10-03)

**What changed**
- The stakeholder asked that, in iteration 2, the observer feedback updates the four Ensemble files, the system decides what goes where, and the rebuild runs from the updated files, visibly in the build page's steps and logs.
- Recorded as D-36 and A-4 (FR-RB-6 amended, FR-RB-7 and FR-RB-8 added). Routing is real and deterministic, using the boundary rule sets, and logged as a simulated LLM call. Segments are appended verbatim, so every log line is true (D-5 still holds: the outcome stays scripted).
- Iteration 2's phase 1 now opens with "Apply observer feedback": one routing sub-step and one sub-step per core file. No phase, weight or test id changes.

**Files**
- CHANGE docs/requirements.md (FR-RB-6 to FR-RB-8, A-4), docs/decisions.md (D-36), docs/build-simulation.md (phase 1 row, §9), docs/implementation-plan.md (M10), docs/ui-spec.md (§2, §3)

**Gates**
- No code changed. Assertions edited: none.

**Notes for next milestone**
- Built in M10. M5 only needs the iteration 2 script to have room for these sub-steps; the routing itself, and its tests, land in M10 with the boundary rule sets from M5.
- Assay's weight (6, about 4.5 s at 1x) now holds the routing steps in iteration 2. M10's 1x hand check judges whether that is readable; if not, a weight change is an amendment.

### M2: Frontend shell and design system (2026-10-03)

**What changed**
- SeedFoundry now looks like Seed v0.1: its colour, type, radius and motion tokens are in `tokens.css`, unchanged, with light on `:root` and dark under `[data-theme='dark']`. Inter and JetBrains Mono are bundled from npm and served with the app.
- The values the Seed docs leave out (shadows, easing, chart grid and brush, scrollbar, font stacks, space steps) are filled from the existing palette, and the build console has its own dark tokens in both themes, including `--console-api` for API lines (D-37).
- The app shell: the SeedFoundry wordmark on the left, the journey indicator (Knowledge, Build, Review, Seed) held at the centre by a three-column grid, and on the right the "Iteration 1 of 2" badge once a build exists, then the theme toggle. Knowledge is a link; Build, Review and Seed show the current step but are not links yet.
- Routes `/knowledge` (`/` goes there), `/build/1|2`, `/review/1|2`, `/seed`, each with a placeholder inside the shell. Any other path goes to `/knowledge`. The dashboard stays a query string on the review route (OQ-4).
- Theme: a first visit follows the OS; the toggle switches and remembers under `seedfoundry.theme`; it still works where storage is blocked. A small inline script in `index.html` sets the theme before the first paint.
- Base components: button (primary, secondary), chip (five tones), card, modal (focus moves in and is trapped, Escape closes, focus goes back to the opener, a backdrop click does not close it), tooltip (hover and keyboard focus, linked by `aria-describedby`).
- The shell reads `GET /api/state` and follows `GET /api/events`; any newer event or a `stream.resync` re-fetches the snapshot (D-38).
- Tests: the contrast test (Seed v0.1's rules over both themes, plus the console pairs, plus a check that the Seed values in `seed-reuse-notes.md` §1.3 are still the values in `tokens.css`); routes and journey; iteration badge from a snapshot with a build; theme; base components; the live store; the event type contract against the backend's `EVENT_TYPES`; and the network check over `src/`, which also runs as `postbuild` over `dist/`.

**Files**
- CHANGE frontend/src/styles/tokens.css (tokens, D-37)
- NEW frontend/src/styles/base.css, src/theme.ts, src/router.ts, src/events.ts, src/stores/lab.ts
- NEW frontend/src/components/base/ (BaseButton, BaseChip, BaseCard, BaseModal, BaseTooltip), src/components/shell/ (TopBar, JourneyIndicator, IterationBadge, ThemeToggle), src/components/ScreenPlaceholder.vue
- NEW frontend/src/views/ (KnowledgeView, BuildView, ReviewView, SeedView)
- CHANGE frontend/src/App.vue (shell), src/main.ts (fonts, styles, theme, router, store), index.html (theme before paint)
- NEW frontend/scripts/check-network.ts
- CHANGE frontend/package.json (vue-router, both font packages, `postbuild`), package-lock.json, tsconfig.json (`scripts/`)
- NEW frontend/tests/contrast.spec.ts, shell.spec.ts, theme.spec.ts, components.spec.ts, lab-store.spec.ts, events-contract.spec.ts, network.spec.ts, helpers.ts
- CHANGE frontend/tests/smoke.spec.ts (assertion changed by D-39)
- DELETE frontend/src/components/.gitkeep, src/stores/.gitkeep, src/views/.gitkeep
- CHANGE docs/decisions.md (D-37 to D-39), docs/seed-reuse-notes.md (§1.6 as built; §10 rows 8, 10, 11), docs/build-simulation.md (§4 as built), docs/implementation-plan.md (M2 status; as-built note), docs/CLAUDE.md (build command comment), docs/project-notes.md (this entry)

**Gates**
- backend: 86 passed, frontend: 128 passed (through `python run.py test`)
- `npm run build`: typecheck, build and `postbuild` network check pass. The bundle's only URL-like strings are three XML namespaces and Vue's error-reference link, all allowed by name
- Checked that the tests can fail: a darker dark `--text-muted`, a light-theme `--console-api` and a one-digit change to `--chart-anomaly` each failed the contrast test; a Google Fonts `@import` added to the built CSS failed the dist check; a `fetch()` to another host added to `main.ts` made `npm run build` exit 1. All reverted.
- contrast: every pair passes in both themes with Seed v0.1's values unchanged. The tightest is light `anomaly` under its light label at 4.50:1
- determinism: not yet applicable (from M5) | no-em-dash: no test yet (from M3); every file written in M2 was searched and has none | network: tested over `src/` and enforced over `dist/`
- assertions edited: one, the M0 smoke test, by D-39 (the placeholder `h1` it checked no longer exists; it now checks the shell's wordmark)

**Hand checks**
- `python run.py` started both processes and printed the ready line. Through `http://127.0.0.1:5273`: `/`, `/knowledge`, `/build/1`, `/review/2` and `/seed` answered 200; the page carries the theme script; `/api/state` returned the empty snapshot; `/api/events` opened the stream; the Inter font file was served from `node_modules` as `font/woff2`. Ports were free after stopping. Checked over HTTP from the terminal, not in a browser window.
- Waiting on the stakeholder, in a browser: the theme toggle in both directions, a reload keeping the theme, a first visit following the OS theme with storage cleared, the journey indicator on each route, visible keyboard focus on every control, and the tokens matching Seed v0.1.

**Decisions and questions**
- New: D-37 (token gaps, chart labels, console tokens), D-38 (router, routes, theme boot, live store, event types, network check, contrast test source), D-39 (M0 smoke assertion)
- Opened: none. Closed: none.

**Notes for next milestone**
- The base components are not on any screen yet; M3 is the first to use them (editor toolbar, import dialog in `BaseModal`, the mic tooltip).
- `stores/lab.ts` has no reducers: every newer event re-fetches the snapshot. M3 should add intake reducers (events carry no content, so re-fetch a file after an `intake.file_updated` whose `changed` includes `content`), and M5/M6 must add build reducers before log events arrive several times a second.
- Build, Review and Seed in the journey indicator become links in M6, M9 and M11 (`LINKED` in `JourneyIndicator.vue`).
- Charts (M7) read `--chart-<role>` and the three `--chart-label-on-*` tokens at paint time and repaint on theme change; `theme` in `src/theme.ts` is a ref they can watch.

### M3: Intake page (2026-10-03)

**What changed**
- The Knowledge page replaces its placeholder: the editor on the left (about 70%), the file panel on the right (about 30%), in the M2 tokens with no new colour.
- Editor: name field and category picker above it; Edit / Preview toggle; a mic button with a "Voice input" tooltip that does nothing; an overflow menu with Rename, Change category and Delete. Edit is a plain textarea in JetBrains Mono.
- Preview renders headings, lists, tables, code, emphasis and links. It cannot run or fetch anything: raw HTML shows as text, images show as an "Image" label with their alt text and address, and links show their text and address but are not followed (D-40). Two layers: `markdown-it` with HTML off, then DOMPurify with an allowlist.
- Files: new file, rename, change category, and delete with a confirmation. A second file in a core category, by create, import or category change, asks "Replace it?" naming the current file, then sends `replace`; the server's 409 is the backstop and asks the same question in its own words.
- Autosave 800 ms after typing stops, and at once on file switch, on leaving the page and before Start Build. The unsaved dot shows on the file until the server has the text. Small drafts go out with `keepalive` when the tab closes; a larger one makes the browser ask first. The echo of your own save never overwrites what you typed since (D-41).
- File panel: the core checklist (a slot needs a file with something other than whitespace, D-42), Start Build with a "Missing: ..." tooltip, then the files in Ensemble order with "Add file" in empty categories. Categories, labels, descriptions and filename hints all come from the server.
- Import: one row per file, category pre-selected from the server's hints, "Replaces existing person.md" where it applies, and two files for the same core category block Import until one changes. One raw request per file; 413 and 415 messages show on their row as the server wrote them.
- Empty state: one line on each of the four Ensemble files, with New file and Import.
- During a build the page is read-only with a banner and a link to the build; a save refused with 409 `intake_locked` keeps its text and is sent again when the build ends.
- The lab store applies intake events in place instead of re-fetching the snapshot, and fetches a file's content only when someone else changed it.
- The selected file is in the URL, so a refresh opens it again.
- The no em dash test now runs over frontend, backend, tests, launchers and docs (`docs/seed_docs/` excluded).

**Files**
- NEW frontend/src/api.ts, src/intake.ts, src/markdown.ts, src/stores/intake.ts
- NEW frontend/src/components/base/BaseMenu.vue, BaseConfirm.vue
- NEW frontend/src/components/intake/ (FileEditor, FilePanel, MarkdownPreview, NewFileDialog, ImportDialog, EmptyState)
- CHANGE frontend/src/views/KnowledgeView.vue (the page), src/stores/lab.ts (intake reducers, D-41), src/components/base/BaseButton.vue (`explainDisabled`)
- CHANGE frontend/scripts/check-network.ts (templated hosts in `dist/` only, D-45)
- CHANGE frontend/package.json, package-lock.json (`markdown-it`, `dompurify`)
- NEW frontend/tests/markdown.spec.ts, knowledge.spec.ts, intake-store.spec.ts, fake-server.ts, fixtures/ (person.md, instrument-awareness.md, environment.md, music.md, vendor-notes.md, hostile.md)
- CHANGE frontend/tests/shell.spec.ts (assertion moved by D-43), tests/network.spec.ts (new cases)
- CHANGE backend/seedfoundry/state.py (`CATEGORY_DESCRIPTIONS`), backend/seedfoundry/main.py (categories endpoint serves them)
- NEW backend/tests/test_no_em_dash.py; CHANGE backend/tests/test_intake_api.py (new test)
- CHANGE docs/decisions.md (D-40 to D-45, OQ-16, pointers on D-35 and D-38), docs/ui-spec.md (§2 as built), docs/implementation-plan.md (M3 status; as-built note), docs/project-notes.md (this entry)

**Gates**
- backend: 90 passed, frontend: 216 passed (through `python run.py test`); the frontend suite passed three runs in a row
- `npm run build`: typecheck, build and `postbuild` network check pass. The bundle's URL-like strings are the XML namespaces, Vue's error-reference link and two `http://${...}` templates in `markdown-it`'s linkify code (D-45)
- FR-IN-1 to FR-IN-11 each have tests named for them in `knowledge.spec.ts`, `markdown.spec.ts` and `intake-store.spec.ts`; FR-IN-10 across a server restart is also the M1 test `test_file_survives_a_real_server_restart`
- Checked that the tests can fail: raw HTML switched on fails the R-7 test (the sanitiser still strips every hazard); HTML on with the sanitiser bypassed fails four; the typographer switched on fails the em dash test; links rendered with `href` fail; fetching on every own save fails the echo test; an em dash added to `SeedView.vue` fails the no em dash test. All reverted
- determinism: not yet applicable (from M5) | no-em-dash: test passes | network: tested over `src/`, enforced over `dist/`
- assertions edited: one, the M2 route test's `/knowledge` row, by D-43 (it checked the placeholder M3 replaces; it now checks that the Knowledge page renders in the shell)

**Hand checks**
- `python run.py` started both processes with `var/` empty. Through `http://127.0.0.1:5273/api` (the Vite proxy): the categories endpoint served labels and descriptions; the four core fixtures and `vendor-notes.md` imported with their hinted categories; a second Person file got 409 `core_slot_taken` naming `person.md`; a new file was created, renamed, refused a move into the filled Music slot (409), and deleted (204); a 1,048,577-byte file got 413 `file_too_large`, a Latin-1 file 415 `not_utf8_text`, and `notes.txt` 415 `not_markdown`, each with its message. An SSE client on the same proxy saw 6 created, 1 updated and 1 deleted event. `/knowledge?file=f-1` answered 200.
- Stopped and started again: all five files were still there, and `music.md` matched the fixture byte for byte. Ports were free after each stop; `var/state.json` was then removed so `var/` starts empty.
- Checked over HTTP from the terminal, not in a browser. Waiting on the stakeholder, in a browser: see the M3 report.

**Decisions and questions**
- New: D-40 (Preview: markdown-it and DOMPurify, images and links as text), D-41 (textarea, autosave, drafts, own-save echo, intake reducers), D-42 (page rulings: whitespace-only slots, selection in the URL, Start Build in M3, import clashes, replace question, name and category controls, New file defaults, category descriptions, banner), D-43 (shell test assertion), D-44 (no em dash test scope), D-45 (templated hosts in the `dist/` network scan)
- Opened: OQ-16 (should file names be unique? assumed no). Closed: none.

**Notes for next milestone**
- M4's Shift shortcuts must be ignored in the Knowledge page's name field and textarea (they are plain `input` and `textarea`), and in the import dialog's selects.
- M4's "Load sample Seed" and "Clear intake" can go through the intake API; the page follows the events, and a file the user is editing keeps their unsaved text (D-41).
- M5's T-01 "core files present" should use the same rule as the checklist: a file with something other than whitespace (D-42 (a)). M5/M6 replace M3's Start Build note with FR-B-1 (create the build, open `/build/<iteration>`); `intake.flushAll()` should still run first.
- M5/M6 add build reducers to `stores/lab.ts`: today any non-intake event still re-fetches the snapshot.
- M10's rebuild modal can reuse `components/intake/FileEditor.vue`'s parts (`MarkdownPreview`, the mic button); the editor itself reads a file from the store, so the modal needs a version that edits a local draft.
- NFR-3 (1 MB in the editor) is a browser check: jsdom cannot measure typing latency. M12's performance pass should time it.

### M4: Demo controller and sample Seed (2026-10-03)

**What changed**
- A hidden demo controller: Shift+O shows a small "Demo" panel bottom right, with a button for every action, each showing its shortcut. The shortcuts work with the panel hidden, and are ignored in any text field, in the editor and name field, in a modal that is not theirs, and (Shift+Enter) on a focused button (D-47).
- Load sample Seed (Shift+P) fills Knowledge with a License Optimization sample: person.md, instrument-awareness.md, environment.md, music.md and vendor-notes.md. On an empty intake it loads at once; otherwise it asks first and replaces every file, Misc Context included (OQ-17). The four core slots complete and Start Build turns on.
- Clear Knowledge (Shift+C) and Reset to start (Shift+R) ask first. Reset removes files, builds and the approval and goes back to Knowledge; speed and theme stay. Shift+D switches the theme; Shift+Enter does what Start Build does today (saves and says builds arrive in M5).
- Stubs that say so and do nothing else: Skip phase and Skip to end (M5), Prefill feedback (M10; its shortcut cannot fire until the rebuild modal exists). Speed 1x/2x/4x is remembered in the browser and shown as pressed, for M5 to use.
- The server does the work (`/api/demo/sample`, `/clear`, `/reset`) under the intake rules (409 `intake_locked` during a build, except Reset), with the normal intake events plus a new `demo.reset`, so every open page follows (D-46).

**Files**
- NEW backend/seedfoundry/sample/person.md, instrument-awareness.md, environment.md, music.md, vendor-notes.md
- CHANGE backend/seedfoundry/sample/__init__.py (`SAMPLE_FILES`, `sample_files()`)
- NEW backend/seedfoundry/demo.py
- CHANGE backend/seedfoundry/main.py (`/api/demo/*`), intake/files.py (`check_unlocked` made public; "sample" source), events.py (`demo.reset`)
- NEW backend/tests/test_demo_api.py, test_sample.py
- NEW frontend/src/demo/DemoController.vue, shortcuts.ts, api.ts; frontend/src/stores/demo.ts
- CHANGE frontend/src/App.vue (mounts the controller), src/events.ts (`demo.reset`), src/stores/intake.ts (`startBuild`, `buildNote`, `discardMissing`), src/views/KnowledgeView.vue (uses the store's Start Build)
- NEW frontend/tests/demo.spec.ts, shortcuts.spec.ts; CHANGE frontend/tests/fake-server.ts (demo endpoints, serving the real sample)
- CHANGE docs/decisions.md (D-46, D-47, OQ-17), docs/ui-spec.md (§8 as built), docs/build-simulation.md (§3, §8 as built), docs/seed-reuse-notes.md (§5.7, §6.2 as built), docs/implementation-plan.md (M4 status; as-built note), docs/project-notes.md (this entry)

**Gates**
- backend: 114 passed, frontend: 271 passed (through `python run.py test`)
- `npm run build`: typecheck, build and `postbuild` network check pass
- Exit criteria: Load sample fills intake with the four core slots complete (API: `test_load_sample_fills_the_four_core_slots`; page: "fills an empty intake at once: the four core slots complete and Start Build enabled"). Every shortcut has a page test; capital P, C, R, D (and O, S, E, F, Shift+1, Shift+Enter) typed in the editor and the name field do nothing; a select and a contenteditable element likewise; Shift+O toggles; Shift+1/2/4 match by code whatever the character (`!`, `1`, `&`; `@`; `$`)
- Sample: deterministic (`test_loading_the_sample_is_deterministic`: two fresh labs give the same files, ids, content hashes and events, seq and `wall_ts` aside; a reload changes only the ids); every Ensemble section present, read from `ensemble/ensemble_context.md` (`test_each_core_file_has_every_ensemble_section`); D-36's routing targets present; line ends normalised (`core.autocrlf` is on here, so a checkout can give the files CRLF)
- Checked that the tests can fail: the text-field rule removed failed 9 tests; digits matched on the character failed 3; the modal rule removed failed 4; Load sample without its confirm failed 3; dropping the unsaved-draft cleanup failed 1 (that test first passed without it, because switching files already drops the open file's draft, so it was rewritten to put the draft on a file that is not open). All reverted
- determinism: not yet applicable to builds (from M5); the sample's own test passes | no-em-dash: pass, and covers the sample files (`test_the_no_em_dash_scan_covers_the_sample`) | network: pass
- assertions edited: none

**Ensemble boundary self-review** (build-simulation §6.1; the lint itself is M5's). Each file was read against each rule, then searched for the obvious words of each rule:

| Rule | Searched for | person.md | instrument-awareness.md | environment.md | music.md | vendor-notes.md |
|---|---|---|---|---|---|---|
| B-DATA (outside environment.md) | schema, column, field, mapping, file paths, record ids, SAP, records, rows | clean | clean | n/a (its home) | clean | clean |
| B-SEC (person.md, music.md) | security, access, guardrail, permission, credential, privacy, protect, safety, compliance, audit, risk | clean | n/a | n/a | clean | n/a |
| B-UI (outside environment.md) | colour, theme, layout, navigation, screen, page, button, click, font, palette, chart, dashboard, display, red, green, style | clean | clean | n/a (its home) | clean | clean |
| B-MODEL (outside instrument-awareness.md) | token, context, model, prompt, LLM, hallucination, truncation | clean | n/a (its home) | clean | clean | clean |
| B-LOGIC (environment.md) | prioritise, priority, rank, score, decision, decide, recommend, threshold, should, must, candidate | n/a | n/a | one hit: "Optimisation candidates", Seed v0.1's panel title in User Experience, not a rule | n/a | n/a |

Choices made to keep it clean: the classification thresholds and the leaver rule sit in music.md, and environment.md's Data Layer only says the class is "as music.md defines"; the Leaver class is not called an access finding in music.md (B-SEC); person.md says "frameworks", not "mental models" (B-MODEL); environment.md says "situation", not "context". M5's lint should allowlist panel titles such as "Optimisation candidates".

**Hand checks**
- `python run.py` started both processes. Through `http://127.0.0.1:5273/api` (the Vite proxy), on the existing intake (one file): Load sample without `replace` got 409 `intake_not_empty` ("Knowledge has 1 file. Loading the sample Seed replaces them all."); with `replace` it gave the five files in Ensemble order; Clear deleted 5; Load sample again 201; Reset removed 5 files and 0 builds, and a second Reset changed nothing. An SSE client on the proxy saw every step in order: 1 delete then 5 "Loaded ..." creates, 5 deletes, 5 creates, 5 deletes then `demo.reset`, 5 creates. `/knowledge` answered 200.
- Stopped and started again: the five sample files were still there, each with the same SHA-256 as before the restart; seq carried on (42). Ports were free after each stop.
- `var/state.json` was copied aside before the check and put back afterwards, so Knowledge holds what it held before M4 (one file, `KICKOFF_PROMPT.md`).
- Checked over HTTP from the terminal, not in a browser. Waiting on the stakeholder, in a browser: Shift+O shows and hides the panel; Load sample fills the Knowledge page live; the four sample files read like a real Ensemble bundle; Clear and Reset ask first; capitals typed in the editor and the name field trigger nothing; every panel action by keyboard; both themes.

**Decisions and questions**
- New: D-46 (server endpoints, Load sample and replace, Reset's scope, `demo.reset`, the sample's load order and bytes), D-47 (shortcut rules, panel focus, stubs, speed in the browser, shared Start Build, "Clear Knowledge" on screen)
- Opened: OQ-17. Closed: OQ-17 (replace all, ask first; stakeholder, 2026-10-03)

**Notes for next milestone**
- M5: speed lives in `stores/demo.ts` (`speed`, 1, 2 or 4); send it to the engine and keep it there across Reset. Skip phase and Skip to end are wired to `unavailable()` in `stores/demo.ts`: give them real actions and make them available only while a build runs.
- M5: Reset to start (`demo.reset()` in `demo.py`) removes a running build's record but there is no engine to stop yet; the engine must be cancelled first, and the client should then leave the build page (Reset already routes to `/knowledge`).
- M5: replace `intake.startBuild()` (M3's note) with FR-B-1; Shift+Enter already calls it. `intake.flushAll()` should still run first.
- M5's boundary lint must give zero on the sample (see the self-review above for the words that were avoided). Its Assay coverage can read a file's `##` headings against the section names in `ensemble/ensemble_context.md`, as `test_sample.py` does.
- M7: the generator follows the class rules and fields in the sample (seed-reuse-notes §5.7 as built): `days_active` per month, `assignee_status`, the 1 to 11 and 12-or-more thresholds, and the departments named in environment.md's Adaptation Layer.
- M10: the rebuild modal marks itself `data-modal="rebuild"` so Shift+F reaches it, and its editor is a textarea, so typing there is already safe. Route feedback to the `##` sections listed in build-simulation §8 as built.
- M12: the operator guide's shortcut table is `SHORTCUTS` in `frontend/src/demo/shortcuts.ts`.

### M5: Beat engine, phases and simulated clients (2026-10-03)

**What changed**
- Start Build (button or Shift+Enter) now starts a real build and opens `/build/<iteration>`. The build runs all 11 phases with their sub-steps and tests T-01 to T-21, 220 events for the sample, in 75 s of simulated time: 75.0 s at 1x, 18.75 s at 4x. Until M6 the build page is the placeholder with one live line ("Build running: phase 3 of 11, Synthesis. ...", OQ-18).
- Knowledge is read-only while the build runs and free again when it ends; Reset stops a running build first; a server restart mid-build marks it interrupted (D-33).
- The demo controller's Speed (1x, 2x, 4x) is kept on the server and survives Reset; Skip phase and Skip to end work while a build runs. They change pacing only: the events are the same at any speed and with any skips (D-48).
- Real work: Assay inventory, Ensemble coverage and fingerprint, the boundary lint (five rules, zero on the sample, D-50), the manifest and upload checksums, Planting's heading summary and declared stack, and the three Seed v0.1 gates auto-resolved in phase 8 citing the section they used. LLM and Seed API calls go through simulated clients and say "(simulated)" (D-22).
- Honest gaps: T-08 and T-13 to T-20 report "not run" until M7 and M9, raise no finding and claim no pass (D-51). Iteration 2 can be started by API only, and its feedback sub-steps read the feedback and say that nothing was routed until M10 (D-52).
- A completed build keeps its own events with its record, so they survive a restart (D-49, answering D-31).

**Files**
- NEW backend/seedfoundry/engine/catalogue.py, script.py, runner.py, clock.py
- NEW backend/seedfoundry/clients/llm.py, seed.py; CHANGE clients/__init__.py
- NEW backend/seedfoundry/intake/assay.py, boundary.py, feedback.py
- NEW backend/seedfoundry/generate/outline.py
- CHANGE backend/seedfoundry/state.py (build record, `next_build_id`, `apply(..., then)`, snapshot without logs), main.py (`/api/builds`, `/api/builds/{id}/events`, `/api/demo/speed`, `/api/demo/skip`; Reset stops the engine)
- NEW backend/tests/test_assay.py, test_boundary.py, test_engine.py, test_build_api.py
- NEW frontend/src/builds.ts; CHANGE frontend/src/events.ts (`BUILD_EVENT_TYPES`), stores/lab.ts (build reducers, `upsertBuild`, `build`), stores/intake.ts (`startBuild` calls the server), stores/demo.ts (speed and skip), demo/api.ts, demo/DemoController.vue, views/KnowledgeView.vue, views/BuildView.vue
- NEW frontend/tests/build-view.spec.ts; CHANGE frontend/tests/lab-store.spec.ts, events-contract.spec.ts, demo.spec.ts, knowledge.spec.ts, fake-server.ts
- CHANGE docs/decisions.md (D-48 to D-53, OQ-18, OQ-19; notes on D-31, D-46), docs/build-simulation.md (§1, §2, §3, §4, §6.1, §9 as built), docs/ui-spec.md (§3, §8 as built), docs/seed-reuse-notes.md (§4.2, §6.2 as built), docs/implementation-plan.md (M5 status; as-built note), docs/project-notes.md (this entry)

**Gates**
- backend: 181 passed, frontend: 284 passed (through `python run.py test`)
- `npm run build`: typecheck, build and `postbuild` network check pass
- Exit criteria: determinism (`test_two_runs_at_different_speeds_and_with_skips_give_the_same_stream`: a 1x run and a run at 4x, 2x and 1x with three phase skips and a skip to end give the same full event stream, `wall_ts` aside, and the same kept log; also `test_speed_and_skip_do_not_change_the_events` over HTTP); clock (`test_a_build_at_1x_takes_75_simulated_seconds`: last `sim_t` 75.0, fake clock 75.0 s; `test_weights_sum_to_100_over_a_75_second_budget`); boundary lint (each rule flags a planted line in a wrong file and none in its home; zero on the sample); phases and events (every phase, sub-step and test id in order for both iterations, checked against build-simulation §2's table; gates in phase 8 with their citations; types in `EVENT_TYPES` and the frontend contract); speed, skip, Reset during a build, intake lock and release, and restart mid-build with the real engine (`test_a_server_restart_mid_build_marks_it_interrupted`): each tested
- Checked that the tests can fail: speed written into event data failed both determinism tests and the speed tests; Reset without stopping the engine failed the Reset test (it first passed, as the engine's own guard ends an orphaned build when it next wakes, so the test now starts a new build at once, which the still-running old task would refuse); the lint without its allowlist gives one B-LOGIC advisory on the sample ("Optimisation candidates"), which the zero-findings test catches. All reverted
- determinism: pass | no-em-dash: pass, and every message and string in a full build's events, both iterations, is checked (`test_no_em_dash_in_a_full_builds_log`) | network: pass
- assertions edited: five frontend assertions that described M3/M4 stubs (D-53): Start Build in `knowledge.spec.ts` and `demo.spec.ts`, Speed's message and "no request", Shift+S/E's M5 message, and the Reset test's request list (it now includes the speed sent before Reset)

**Hand checks** (terminal, through the Vite proxy at `http://127.0.0.1:5273`; `var/state.json` backed up first and restored after, same SHA-256)
- 4x: Load sample, Start Build: 220 events in 18.75 s, ending at `sim_t` 75.0; the log reads in order and sensibly (sample lines are in build-simulation §4 as built).
- 1x end to end: 75.02 s from the request to `build.completed`; each phase started on its schedule (Distillation 4.52 s, Seeding & Life 44.27 s, Teardown 70.53 s). Mid-build, creating a file and Load sample were refused with 409 `intake_locked` ("Knowledge files are read-only while a build runs."); after it, a file could be created. The snapshot leaves the log out and `GET /api/builds/b-2/events` served all 220 events.
- Speed and skips mid-build: 2x and 4x took effect at once; Skip phase completed Distillation 109 ms after the client sent the request, and Skip to end completed the build 62 ms after it (both through the proxy, HTTP and SSE included; the engine's own waits are at most 50 ms, tested). The event content equalled the 1x run's, seq, `wall_ts` and build id aside. Skip with no build: 409 with "No build is running, so there is nothing to skip."
- Reset mid-build (in Distillation): 5 files and 1 build removed; the seq did not move in the 3 s after it; speed was kept; the sample loaded and a new build started at once.
- Restart mid-build: the launcher's process tree was killed in Distillation (state on disk: `running`); after relaunching, the build read `interrupted`, Knowledge was writable, speed was back to 1x (held in memory, D-48), and a new build ran.
- A browser tab was connected to the stream during the checks, but nothing was checked in a browser. Waiting on the stakeholder, in a browser: Start Build and Shift+Enter open `/build/1`; the build route's line follows the phases and then reads completed; Knowledge shows the read-only banner during the build and not after; the demo controller's Speed buttons show the server's speed after a reload, and Skip phase and Skip to end are disabled with a reason when no build runs and work while one does.

**Decisions and questions**
- New: D-48 (engine, clock, pacing, speed and skip), D-49 (build API and record; a completed build keeps its log, answering D-31; iteration 2 by API), D-50 (boundary lint and coverage), D-51 (not-run tests, phase results, outlines until M11), D-52 (iteration 2 before M10 routing), D-53 (frontend in M5 and the five changed assertions)
- Opened: OQ-18 (what the build route shows until M6), OQ-19 (Start Build when the iteration already has a completed build: run again, replacing it, as built; or refuse)
- Closed: none

**Notes for next milestone**
- M6: the snapshot's build has `plan` (phases, sub-steps and tests for its iteration) and `phase`; the stepper can draw pending phases from it. `GET /api/builds/{id}/events` returns `{build_id, status, seq, events}`: the whole log of a running build (from memory) or a completed one (kept). Load it, then follow `/api/events?after=<seq>`, skipping events already held. The lab store already applies build events in place, so the console can keep its own list from the same stream.
- M6: phase results are `passed`, `findings`, `incomplete` and `failed` (`phase.completed` `data.result`); "incomplete" (a test not run) needs a look until M9 makes it rare. Test statuses include `warn` (T-02, T-03 advisories) and `not_run` (level TEST).
- M7: T-08 is waiting for the alternate dataset (`engine/script.py`, `data_swap`).
- M9: the validators replace `pending(...)` in `engine/script.py` STEPS for T-13 to T-20; findings go out as `finding.raised` with the FR-T-7 fields, as the boundary advisories do. `build.completed` has no verdict yet, and `report.ready` is not emitted.
- M10: iteration 2 starts with `POST /api/builds {"iteration": 2}`; Start Rebuild should save the feedback file, then call it. Replace `feedback_route` and `feedback_update` in `engine/script.py` with D-36's routing, using the boundary rules' patterns in `intake/boundary.py`; a beat that edits a file will need a state change carried with its events (the runner applies only events today).
- M11: `generate/outline.py` drafts the headings; fill the sections there, and the manifest, checksums and Planting's summary follow.

### M6: Build page, stepper and console (2026-10-03)

**What changed**
- `/build/1` and `/build/2` show that iteration's latest build. On the left: a header (iteration chip, Seed name, Elapsed, progress bar, current phase), then the stepper of all 11 phases, pending ones shown from the start. On the right: the console. Everything on the page comes from the build record and its events, and every time from `sim_t`, so the page reads the same at any speed (D-54).
- Stepper: the active phase is open on its sub-steps (pending, active, done with its summary). A finished phase is one line with its simulated duration and a result chip: Passed, Findings: n, Failed: T-nn, or Incomplete: n of m not run. Incomplete is neutral grey, so it reads as neither a pass nor a fault. Finished phases open and close on click, Enter or Space. Iteration 2 shows its five feedback sub-steps first, under "Apply observer feedback".
- Console: `mm:ss.s  LEVEL  message` on the dark console surface, coloured by level, red only for FAIL. One line per build event except `step.started` and `step.completed`, which the stepper shows (132 lines for the sample's iteration 1). It has a level filter (TEST includes PASS; INFO only under All), and Pause/Resume; scrolling up also pauses.
- Refresh and reconnect: the page loads the build's events and follows the stream, keeping both by seq, so no line is missing or doubled. A gap, a `stream.resync`, a Reset or a restart loads the events again and fills the gap. A page that is watching when the server restarts keeps its lines and adds the interruption. Nothing fetches the snapshot per event.
- On completion, until M9: a "Build completed" summary sits above the collapsed stepper, with no verdict. View Dashboard, Rebuild (iteration 1 only) and Approve are present; each says which milestone brings it. The console can be hidden and shown again (OQ-21).
- A route with no build says so and points to Knowledge, or for iteration 2 to iteration 1 (closes OQ-18). An interrupted build says it stopped, gives the server's reason and offers Go to Knowledge.
- Backend: the build record carries `sim_seconds` (75.0), so progress is `sim_t / sim_seconds`. That is the only backend change; no event changed.

**Files**
- NEW frontend/src/stepper.ts, stores/buildLog.ts, components/build/PhaseStepper.vue, BuildConsole.vue, BuildSummary.vue
- CHANGE frontend/src/views/BuildView.vue (the page), stores/lab.ts (`onEvent`, `refreshes`, `sim_seconds` on `Build`), builds.ts (`buildsApi.events`)
- NEW frontend/tests/stepper.spec.ts, build-script.ts; CHANGE frontend/tests/build-view.spec.ts (rewritten for the page), shell.spec.ts, demo.spec.ts, fake-server.ts (serves a build's events)
- CHANGE backend/seedfoundry/state.py (`Build.sim_seconds`), engine/script.py (sets it); backend/tests/test_build_api.py (new test)
- CHANGE docs/decisions.md (D-54; OQ-18 closed; OQ-20, OQ-21 raised), docs/ui-spec.md (§3 as built), docs/build-simulation.md (§3, §4 as built), docs/implementation-plan.md (M6 status, as-built note), docs/project-notes.md (this entry)

**Gates**
- backend: 182 passed, frontend: 317 passed (through `python run.py test`)
- `npm run build`: typecheck, build and `postbuild` network check pass
- Exit criteria, each tested in `build-view.spec.ts` and `stepper.spec.ts`:
  - Refresh mid-build: the events load is held while the stream runs ahead, then answers with events that overlap it. The console equals the expected lines with no double, and the stepper equals one derived from the events. A refreshed page also equals a page that watched from the start (lines, phase states, elapsed, progress).
  - A full build streamed to the page fetches `/api/state` once and the build's events once.
  - A gap and a `stream.resync` re-load and fill the lines.
  - A completed build after a restart, an interrupted build, and a page watching across a restart.
  - Phase and sub-step states and every result chip, iteration 2's feedback group, the console format, the level colours (read from the component against D-37), the filter, pause and auto-scroll, the completion hand-off and its stubbed actions, no Rebuild on iteration 2, and keyboard reachability.
- Checked that the tests can fail. Each change below was made, the matching tests failed, and it was reverted:
  - Dropping the seq dedupe failed the refresh, gap and resync tests.
  - Not re-loading on a new snapshot failed the gap, resync and restart tests.
  - Making step events into lines failed 8 tests.
  - A positive chip for incomplete failed the chip test.
  - Following while paused failed the pause test.
- determinism: pass | no-em-dash: pass | network: pass | contrast: pass (no new colour; the console uses only D-37's tokens)
- Assertions edited: three, recorded first in D-54 (h). `build-view.spec.ts`'s placeholder tests were replaced. The `/build/1` and `/build/2` rows of `shell.spec.ts`'s placeholder table moved to their own Build page test. `demo.spec.ts`'s Start Build test now reads the Build page instead of the placeholder line.

**Hand checks** (terminal, through the Vite proxy at `http://127.0.0.1:5273`; `var/state.json` backed up first and restored after, same SHA-256)
- `/build/1` serves the app.
- 1x end to end, with a "refresh" 20 s in: snapshot, then the build's events, then the stream from the snapshot's seq. The union by seq equalled the kept log: 220 events, contiguous, 132 console lines. Last `sim_t` 75.0; 75.00 s wall. The record carries `sim_seconds` 75.0.
- 4x with Skip phase, and 2x with Skip phase then Skip to end, each "refreshed" mid-build. The load overlapped the stream by 6 and 170 events, all dropped; the union equalled the kept log both times; event content was identical across both runs.
- Restart mid-build (killed in Distillation): the build read interrupted, and its events were the single `build.interrupted` line, with `sim_t` null. Restart after a completed build: its 220 kept events were served.
- Reset mid-build: the build and files were removed, and its events answered 404, so the page falls back to "No build for iteration 1 yet".
- Nothing was checked in a browser. Waiting on the stakeholder, listed in the report.

**Decisions and questions**
- New: D-54 (Build page: data and merge by seq, `sim_seconds`, stepper states and chips, header, console lines and filter, completion until M9, route states, three changed assertions)
- Opened: OQ-20 (Elapsed as simulated time), OQ-21 (what a completed build shows until M9)
- Closed: OQ-18

**Notes for next milestone**
- M7: View Dashboard is stubbed in `components/build/BuildSummary.vue` (`WHY.dashboard`). Wire it to `/review/<n>?dashboard=license-optimization` when the dashboard lands.
- M9: `BuildSummary.vue` is the stand-in for the report panel. Replace it, and settle OQ-21: whether completion moves to `/review/<n>` or the report stays on the build page. Phase chips already show `findings` and `failed` with counts and test ids. `finding.raised` events are counted per phase (advisories excluded).
- M10: Rebuild is stubbed in the same file and hidden on iteration 2. The feedback group shows each update step's `step.completed` summary, so a summary such as "+4 lines in Styling" will appear there without a page change.
- M11: Approve is stubbed in the same file.

### M7: Polished License Optimization dashboard (2026-10-03)

**What changed**
- The License Optimization dashboard exists. View Dashboard on a completed build opens it at `/review/<n>?dashboard=license-optimization`, in a thin frame with "Back to report" and the iteration badge. It has five KPIs, the full-width treemap with its class legend, the three charts, Optimisation candidates and the paginated Seats table, titled License Optimization, in Seed v0.1's design system (D-59).
- Data: SeedFoundry's own estate from a seeded generator (D-55). The primary estate is the sample's professional services firm: 13,050 seats, 17 products from 10 vendors, 5 of them unpriced, so the grade is PARTIAL. The alternate is a software company: 5,620 seats, 11 products, 8 vendors, no names in common. Every class is derived from twelve months of generated usage by music.md's rules; the seed is a fixed string per estate, never the clock.
- Query engine on the server (D-56): every figure is aggregated from the seat rows for the current drill path, which every panel follows. Drill from a treemap cell (a leaf drills vendor, product and class in one step, with one crumb naming all three), a bar, or a product in the candidates table, down to a product's class, where the Seats table lists those seats. The path is in the URL, so reload keeps it and the browser's Back pops one step. The drill bar has Back and the breadcrumb.
- Keyboard: Back, crumbs, product cells, sort headers and First/Previous/Next/Last are buttons. Each chart takes focus; the arrow keys choose a drill target, a line under the chart reads it out, and Enter drills.
- Charts are ECharts 6 from npm, in their own chunk. Every colour is read from the tokens when a chart paints, so a theme switch repaints them, and they repaint once the fonts load.
- T-08 runs for real (D-58): the same descriptor and query engine on both estates give structurally valid payloads of one structure. Germination Trial passes, so the sample build reads "13 tests passed, 8 not run" (was 12 and 9): 223 events, 135 console lines.
- Minimal validators, code M9 extends (D-57): numeric reconciliation recounts from the rows; visual QA checks palette, class colours, red for faults, formats, axis names and units, the grid, fonts and contrast against tokens.css. Both pass on the polished dashboard. They stay out of the build until M9.
- Until M9, `/review/<n>` is a stand-in that says the report arrives in M9 and offers View Dashboard and the build summary (OQ-22). Iteration 1 shows the polished dashboard with a line saying the overlay arrives in M8 (OQ-23).

**Files**
- NEW backend/seedfoundry/data/model.py, estates.py, generate.py; CHANGE data/__init__.py
- NEW backend/seedfoundry/dashboard/descriptor.py, query.py, payload.py; CHANGE dashboard/__init__.py
- NEW backend/seedfoundry/validators/numeric.py, visual.py, structure.py, tokens.py, problems.py; CHANGE validators/__init__.py
- CHANGE backend/seedfoundry/engine/script.py (T-08 and Collect dashboard payload), main.py (dashboard and dataset routes, datasets warmed at start)
- NEW backend/tests/test_data.py, test_dashboard.py, test_validators.py, dashboard_fixtures.py; CHANGE backend/tests/test_engine.py
- NEW frontend/src/dashboard/ (types.ts, api.ts, drill.ts, format.ts, tokens.ts, echarts.ts, options.ts), frontend/src/components/dashboard/ (DashboardFrame.vue, DashboardView.vue, DashboardRenderer.vue, DrillBar.vue, KpiPanel.vue, ChartPanel.vue, TablePanel.vue)
- CHANGE frontend/src/views/ReviewView.vue (stand-in and frame), components/build/BuildSummary.vue (View Dashboard), package.json and package-lock.json (echarts), vite.config.ts (ECharts chunk)
- NEW frontend/tests/dashboard.spec.ts, dashboard-units.spec.ts, fake-echarts.ts, fixtures/dashboard/ (nine responses written by the backend); CHANGE frontend/tests/fake-server.ts (serves them), build-script.ts, build-view.spec.ts, shell.spec.ts
- CHANGE docs/decisions.md (D-55 to D-59; OQ-22 to OQ-24; notes on D-51, D-54), docs/seed-reuse-notes.md (§1.2, §1.4, §5.4 to §5.7, §8, §10 as built), docs/ui-spec.md (§1, §3, §4, §5 as built), docs/build-simulation.md (§2, §3, §4, §6.2, §6.3 as built), docs/implementation-plan.md (M7 status, as-built note), docs/CLAUDE.md (fixture command), docs/project-notes.md (this entry)

**Gates**
- backend: 386 passed, frontend: 357 passed (through `python run.py test`)
- `npm run build`: typecheck, build and `postbuild` network check pass with ECharts in the bundle (no external URL in `dist/`)
- Exit criteria:
  - Numeric reconciliation passes on the polished payload: primary and alternate at All products, the primary at all 113 drill levels, and on other pages and sorts. Visual QA passes on both iterations' descriptors (`test_validators.py`).
  - The query engine matches row-level ground truth at every hierarchy level: all products, 10 vendors, 17 products, 85 product classes. A brute-force recount is compared with the KPIs, legend, treemap, footer, bars and candidate rows (`test_the_query_engine_matches_row_level_ground_truth`).
  - Reload keeps the drill path and its crumbs; the browser's Back pops one step at a time; the drill bar Back and a crumb each go one step (`dashboard.spec.ts`).
  - The data meets every constraint in seed-reuse-notes §5.7, and two generations are identical, in this process and in others under three PYTHONHASHSEED values (`test_data.py`).
  - T-08 runs and passes on the sample with the same logic on both estates; it fails when the logic gives the alternate another structure (`test_engine.py`).
- Checked that the tests can fail. Each change below was made, the matching tests failed, and it was reverted:
  - no guard against stale answers;
  - no repaint on a theme change;
  - no repaint when the fonts load;
  - a treemap leaf drilled as three steps;
  - a hard-coded colour in the bar options;
  - the query engine ignoring the class (88 tests);
  - a leaver no longer a Leaver whatever the usage;
  - the Recoverable KPI over Unused and Underused, which is N-3's defect (82 tests);
  - the generator reading the clock.
- determinism: pass | no-em-dash: pass | network: pass | contrast: pass (no new colour; the dashboard source has no colour literal, a test)
- Assertions edited, recorded first in D-58 and D-59:
  - `test_engine.py`: the stubbed-tests test drops T-08 and counts 13 and 8.
  - `build-script.ts` and `build-view.spec.ts`: the sample counts are 13 and 8.
  - `build-view.spec.ts`: View Dashboard is available instead of saying M7.
  - `shell.spec.ts`: `/review/1` and `/review/2` moved from the placeholder table to their own test.

**Hand checks** (terminal, through the Vite proxy at `http://127.0.0.1:5273`; `var/state.json` backed up first and restored after, same SHA-256)
- 4x: Load sample, Start Build: 223 events in 19.0 s, last `sim_t` 75.0, 135 console lines. T-08 PASS with the two estate lines and "payload structure identical"; Germination Trial passed; "Build completed: 13 tests passed, 8 not run; 0 findings, 0 boundary advisories".
- Dashboard endpoint through the proxy:

  | Level | Time | Size |
  |---|---|---|
  | All products | 86 ms | 39 KB |
  | Microsoft | 62 ms | 20 KB |
  | Microsoft 365 E3 | 47 ms | 15 KB |
  | Microsoft › Microsoft 365 E3 › Unused | 57 ms | 14 KB |

  A path the data does not have gave 404 `drill_not_found`.
- Recount by hand from `GET /api/datasets/primary` (13,050 rows), all equal to the payload:
  - Entitled 13,050, Assigned 12,401, Active 8,286, Unused or underused 3,642.
  - Recoverable a year $1,035,384 with 657 seats withheld.
  - The entitlement bars sum to 13,050; the legend shares sum to 100.0; the priced recoverable bars and the candidates' total are both $1,035,384; the footer's classes sum to 13,050.
  - Microsoft › Microsoft 365 E3 › Unused: 260 seats, $112,320.
- Determinism: two requests gave identical payloads. The rows the server serves equal a fresh generation in another process (PYTHONHASHSEED 7).
- The review route with a drill path serves the app.
- Nothing was checked in a browser. Waiting on the stakeholder, in a browser:
  - Open the dashboard from a completed build.
  - Read it beside Seed v0.1's description in seed-reuse-notes §5: does it read as the same dashboard?
  - Drill from the treemap to one product's Unused seats and back.
  - Reload mid-drill, then use the browser's Back step by step.
  - Use the drill bar, the charts and pagination by keyboard only.
  - Check both themes, including a switch with the dashboard open.
  - Time the first render (under 1 s).

**Decisions and questions**
- New: D-55 (data generator and seed rule), D-56 (descriptor, payload, query engine on the server, drill path in the URL, API), D-57 (minimal validators, kept out of the build until M9), D-58 (T-08 real; changed assertions), D-59 (the dashboard on screen; changed assertions)
- Opened: OQ-22 (the review route and Back to report until M9), OQ-23 (View Dashboard in M7; iteration 1 polished with a note until M8), OQ-24 (figures in JetBrains Mono, as Seed v0.1, while the sample environment.md says Inter)
- Closed: none

**Notes for next milestone**
- M8: patch the descriptor in `dashboard/descriptor.py` `descriptor(iteration)`, which returns the polished one for both iterations today. Derive the defect figures in `dashboard/payload.py` by fixed rules over the payload built from the rows, so they hold at every drill level (R-9).
  - `DashboardView.vue` tags its root with `data-variant`; scope `defects.css` under a class set only when the variant is rough.
  - `visual.check` reads colours and fonts from the descriptor. If V-3, V-7 and V-8 are applied through `defects.css`, extend `validators/tokens.py` to read that file too.
  - Remove the frame's iteration 1 overlay line (OQ-23).
  - T-08 checks structure only. The V-1 pie keeps the recoverable panel's data shape, so it stays a pass; keep it so.
- M9:
  - Map `validators` problems to findings (N-1 to N-5, V-1 to V-8) and run them in place of `pending(...)` for T-13 to T-20 in `engine/script.py`.
  - `harvest.collect` already builds the payload.
  - Finding-to-panel highlight can target `[data-panel="<id>"]`.
  - Settle OQ-21 and OQ-22 together: the review stand-in is `views/ReviewView.vue`.
- M10: embed `components/dashboard/DashboardView.vue` in the split view; it takes `drill` as a prop and emits `navigate` and `back`, so the modal can keep its own drill path off the URL.

### M8: Defect overlay, iteration 1 dashboard (2026-10-03)

**What changed**
- Iteration 1's dashboard is the polished dashboard plus a defect overlay, and shows all 14 catalogue defects (FR-D-2, D-13). Iteration 2 is M7's dashboard: its descriptor and payloads are byte for byte M7's (a digest test).
- The overlay is a named list of fourteen patches, one per defect, each tagged with its id, in `dashboard/overlay.py` (D-60). It has three layers:
  - Descriptor patches (V-1 to V-5, L-1): a pie, a red series, an off-palette colour and a second colour for Active, mixed formats, no axis names, a declared 4.5 s latency.
  - Payload rules (N-1 to N-5): fixed rules over the true figures and the rows, so every wrong figure is derived from the data at any drill level. N-1 bars x 1.2, N-2 shares x 1.12, N-3 the KPI over Unused and Underused, N-4 the footer total set to the assigned count, N-5 the largest row counted twice.
  - Styles (V-6 to V-8): `defects.css`, every rule under `.defects-overlay`, which only the iteration 1 dashboard's root carries. The sheet is loaded on demand when a descriptor names it. It holds no colour value: V-8's grey is a border token used as text.
- `GET /api/dashboards/license-optimization/overlay` serves the list, so the descriptor, the overlay and the payload are each inspectable.
- V-3's hex is the only raw colour. It lives in the overlay's descriptor patch, and the renderer draws a descriptor's class colour as given, so SeedFoundry's own source still writes none.
- L-1: the browser waits the declared latency before drawing the treemap, behind a spinner, while every other panel draws at once (NFR-3). It waits on first draw, reload and each drill, not on paging, sorting or a theme switch (OQ-25). The server answers the whole dashboard in one request, so a server-side wait would have held every panel.
- ECharts gains the pie chart; the pie keeps the bar's data shape, so T-08 passes on both iterations.
- The frame's line "Iteration 1's defect overlay arrives in M8, ..." is gone (OQ-23).
- Validators, still out of the build (D-57):
  - `validators/styles.py` reads the sheet a descriptor names; visual QA checks its geometry, fonts and contrast.
  - `validators/latency.py` is T-15.
  - Visual QA reads pie slices and a panel's own class colours.
  - When two panels disagree on one measure, the numeric check now names the panel whose figure is off its recount.
  - Together they find exactly the 14 defects on iteration 1 and nothing on iteration 2. The build still reads "13 tests passed, 8 not run".
- The "Collect dashboard payload" line no longer names the variant ("Collected the License Optimization payload: 11 panels ..."), so a build does not announce its own defects before M9's validators find them.
- Fixtures: one set per iteration (`fixtures/dashboard/iteration-1/`, `iteration-2/`). The fake server serves the set for the iteration asked. `tests/dashboard_fixtures.py` now runs as the script CLAUDE.md names (it could not import the package before).

**Files**
- NEW backend/seedfoundry/dashboard/overlay.py, validators/styles.py, validators/latency.py
- CHANGE backend/seedfoundry/dashboard/descriptor.py (iteration 1 applies the overlay), payload.py (payload rules), __init__.py; validators/visual.py, numeric.py, structure.py, __init__.py; engine/script.py (payload line); main.py (overlay route)
- NEW backend/tests/test_overlay.py; CHANGE backend/tests/test_dashboard.py, test_validators.py, test_engine.py, dashboard_fixtures.py
- NEW frontend/src/dashboard/latency.ts, stylesheets.ts; CHANGE frontend/src/styles/defects.css (the overlay's styles), dashboard/types.ts, format.ts, options.ts, tokens.ts, echarts.ts (pie), components/dashboard/ChartPanel.vue (pie, wait and spinner, class colour on the legend), DashboardView.vue (root class, sheet), DashboardRenderer.vue (level), TablePanel.vue (`data-test="table-scroll"`), DashboardFrame.vue (line removed)
- MOVE frontend/tests/fixtures/dashboard/*.json to iteration-1/ and iteration-2/ (rewritten by the backend); CHANGE frontend/tests/dashboard.spec.ts, dashboard-units.spec.ts, fake-server.ts
- CHANGE docs/decisions.md (D-60, D-61, OQ-23 note, OQ-25), docs/seed-reuse-notes.md (§2.5, §5.8 as built), docs/build-simulation.md (§4, §5, §6.2, §6.3, §6.4 as built), docs/ui-spec.md (§5 as built), docs/implementation-plan.md (M8 status, as-built note), docs/CLAUDE.md (fixture command), docs/project-notes.md (this entry)

**Gates**
- backend: 433 passed, frontend: 376 passed (through `python run.py test`)
- `npm run build`: typecheck, build and `postbuild` network check pass. `defects.css` is its own 0.8 kB chunk, loaded on demand; the ECharts chunk with the pie is 595 kB.
- Exit criteria:
  - The overlay applies only to iteration 1. Iteration 2's descriptor and six payloads equal M7's digests. Iteration 2 has no root class and no spinner, and all its charts paint at once (`test_dashboard.py`, `dashboard.spec.ts`).
  - All 14 defects are present on iteration 1, and each wrong figure equals its rule over the data at 11 sampled drill levels. Nothing else in the payload differs from the polished one (`test_overlay.py`).
  - Each defect is detected at All products by the extended minimal checks, mapped by test, check and panel. Removing any one descriptor or payload patch removes exactly its defect. Iteration 2 gives no problem at four levels.
  - The overlay stays applied at the 11 sampled levels, with only the documented exceptions: N-3 at an unpriced product, Active or Unused; N-4 at a class other than Unassigned.
  - Contrast test passes with no token changed. `defects.css` has only selectors under `.defects-overlay`, no sibling combinator, no token definition and no colour value. Nothing but `stylesheets.ts` imports it. The top bar and the frame sit outside the root class (tests).
  - The rest of iteration 1 renders while the treemap waits: the KPIs, three charts and the Seats rows are drawn before the wait is released (test). Iteration 2 makes no wait. The real render time is a browser check (below).
  - T-08 passes on both iterations; a sample build reads "13 tests passed, 8 not run" (`test_engine.py`, hand check).
- Checked that the tests can fail. Each change below was made, the matching tests failed, and it was reverted:
  - the overlay applied to iteration 2 (144 tests);
  - N-1's factor 1.0 (25);
  - N-5 adding nothing (16);
  - the payload rules not applied (25);
  - one `defects.css` rule unscoped (1);
  - the styles reader ignoring colour (14);
  - cross-panel problems blamed on the table (1);
  - the structure check not knowing the pie (4);
  - the latency ignored (4);
  - a wait on every request (1);
  - no root class (2);
  - the class colour override ignored (2).
- determinism: pass | no-em-dash: pass | network: pass | contrast: pass (no new token)
- Assertions edited, recorded first in D-61:
  - `test_dashboard.py`: the "same for both iterations until M8" test is replaced by iteration 2 equals M7 and iteration 1 equals polished plus overlay. The endpoint test asks for iteration 2. The fixture test covers both iterations.
  - `test_validators.py`: visual QA passes on iteration 2 only.
  - `test_engine.py`: the payload line has no "(polished)".
  - `dashboard.spec.ts`: polished checks open iteration 2; the iteration 1 frame has no M8 line.
  - `dashboard-units.spec.ts`: polished options read iteration 2's fixtures.

**Hand checks** (terminal, through the Vite proxy at `http://127.0.0.1:5273`; `var/state.json` backed up first and restored after, same SHA-256)
- 4x: Reset, Load sample, Start Build. Iteration 1: 223 events in 19.0 s, 135 console lines, last `sim_t` 75.0, T-08 PASS with descriptor `e6a28a`, "Collected the License Optimization payload: 11 panels ...", "Build completed: 13 tests passed, 8 not run; 0 findings, 0 boundary advisories". Iteration 2 by API (`POST /api/builds {"iteration": 2}`): 245 events, 145 lines, T-08 PASS with `abcc42` (M7's), the same completion line.
- Iteration 1 and 2 side by side:
  - The payloads differ only at the candidates total row, the Entitled bars and their keyboard targets, the Recoverable KPI, the legend shares and the Seats footer.
  - The descriptors differ only in the patched fields, plus `variant` and `styles`.
- Each N-defect against a recount from `GET /api/datasets/primary` (13,050 rows), at seven levels, all as the rules say:

  | Level | N-1 bars (KPI) | N-2 shares | N-3 KPI (true) | N-4 footer (class sum) | N-5 total |
  |---|---|---|---|---|---|
  | All products | 15,660 (13,050) | 112.0% | 1,191,396 (1,035,384) | 12,401 (13,050) | 17,250 |
  | Microsoft | 8,016 (6,680) | 112.0% | 456,492 (435,216) | 6,383 (6,680) | 10,880 |
  | Microsoft › Microsoft 365 E3 | 5,040 (4,200) | 112.0% | 216,000 (232,416) | 4,074 (4,200) | 8,400 |
  | Atlassian › Jira Software (unpriced) | 960 (800) | 111.9% | 0 (0): falls away | 768 (800) | 1,600 |
  | Microsoft 365 E3 › Unused | 312 (260) | 112.0% | 112,320 (112,320): falls away | 260 (260): falls away | 520 |
  | Microsoft 365 E3 › Unassigned | 151 (126) | 112.0% | 0 (54,432) | 0 (126) | 252 |
  | Sales Cloud Enterprise › Leaver | 26 (22) | 112.0% | 0 (43,560) | 22 (22): falls away | 44 |

- At every level the descriptor is still rough, with the pie and the 4.5 s treemap.
- Two identical requests gave identical payloads.
- Dashboard requests, best of three: iteration 1 at 80, 53 and 42 ms; iteration 2 at 77, 64 and 51 ms (All products, Microsoft, a leaf); 14 to 39 KB.
- The overlay endpoint lists N-1 to L-1. The review route with a drill path and `defects.css` are served through the proxy.
- Nothing was checked in a browser. Waiting on the stakeholder, in a browser:
  - Open iteration 1's dashboard: would a first-time viewer call it unfinished within five seconds?
  - Find each of the 14 defects on screen, with seed-reuse-notes §5.8's as-built table beside you.
  - Drill on iteration 1 and check the overlay holds; check iteration 2 is still clean.
  - Watch the treemap spinner, and check whether the rest of the page is usable meanwhile. Time iteration 2's first render (under 1 s).
  - Check both themes: the SeedFoundry shell around the rough dashboard stays on the design system.
  - Use drill and pagination on iteration 1 by keyboard only.

**Decisions and questions**
- New: D-60 (the overlay: list, layers, rules, deep-drill behaviour, V-3's colour, scoped sheet, L-1 in the browser, validators extended, payload line, fixtures), D-61 (assertions changed)
- Opened: OQ-25 (when the slow treemap waits again)
- Updated: OQ-23 (the M8 part is done; the line is gone)
- Closed: none. OQ-22 to OQ-24 are unanswered, so their assumptions stand.

**Notes for next milestone**
- M9:
  - Map validator problems to findings by test, check and panel. `defect_of` in `backend/tests/test_overlay.py` is a working mapping:
    - T-16 by panel (entitlement N-1, seats-treemap N-2, k-recoverable N-3, seats N-4, candidates N-5);
    - T-17 V-1;
    - T-18 axis checks V-5, else V-4;
    - T-19 red-for-faults V-2, palette and class-colour V-3, font V-7, grid, overflow and truncation V-6;
    - T-20 V-8;
    - T-15 L-1.
  - Run them in place of `pending(...)` in `engine/script.py`. `harvest.collect` already builds the payload.
  - Several problems make one finding (N-1 alone raises 18 at All products).
  - The D-14 count is on the unfiltered payload.
- M9: the T-15 log line can read the latency problem's message ("Seats by vendor and product responds in 4.5 s (budget 1.0 s)").
- M9: finding-to-panel highlight can target `[data-panel="<id>"]` inside `.defects-overlay`. The "N findings" link goes in `DashboardFrame.vue`, where the M8 line was.
- M10: `DashboardView` carries the overlay itself (class and sheet), so the split view's iteration 1 dashboard is rough with no extra work. Its treemap will wait 4.5 s there too (OQ-25).

### M9: Validators and build report (2026-10-04)

**What changed**
- Every test runs; none is "not run". Stress & Probe and Harvest Validation run real checks:
  - T-13: rules are derived from environment.md's Protection layer, line by line, and ten probes are evaluated against them as Seed v0.1's policy evaluation does (D-62). The sample gives 9 rules from 4 lines and passes.
  - T-14: the seat record contract takes every row of the estate and refuses eleven malformed rows; the drill parser refuses five malformed paths (D-62).
  - T-15 to T-20: the latency, numeric and visual validators run over the iteration's dashboard at All products, its descriptor and its stylesheet.
- Findings (D-63): the validators' problems are grouped into findings by test, check and panel, never by reading the overlay. The sample's iteration 1 build raises exactly N-1 to N-5, V-1 to V-8 and L-1; iteration 2 raises none. Each is raised in the sub-step that finds it, before its test's result, and reads like build-simulation §4 ("N-1 Entitled seats: KPI shows 13,050, product chart sums to 15,660; 18 problems in all").
- Each finding carries its id, category, test, panel and panels (V-3 has two, V-6 five), expected and shown values from the data, severity (Numeric high, Visual and Latency medium, OQ-26), phase and sub-step, a message, and every problem behind it. A problem outside the catalogue would get its own id (N-X1); the sample raises none.
- Test results follow their findings: a high finding fails the test, medium ones warn. A phase fails only when a test failed with no finding for it, so phases 9 and 10 complete as findings on iteration 1 (build-simulation §2). The completion line counts warned tests apart and gives the verdict.
- Validator messages were rewritten to read on their own, with formatted figures; a format problem shows the panel's own figure in both formats.
- The report (D-64) is assembled from the build's kept events and served at `GET /api/builds/{id}/report`, so it survives a restart. It has the verdict (Completed with findings in amber, Passed in green, Failed in red), counts, phases, findings grouped Numeric, Visual, Latency and Boundary, every test, the gates and simulated usage. Compile report emits `report.ready`.
- Report on screen (D-65): `BuildReport.vue` replaces M6's summary on the Build page (which stays on `/build/<n>`, OQ-21) and the stand-in on `/review/<n>` (OQ-22). It is embeddable for M10. Rebuild and Approve still say M10 and M11.
- Each dashboard finding links to the dashboard at All products with `finding=<id>`: its panels are outlined in the accent, the frame says which finding is shown and takes focus, a reload keeps it and a drill drops it. Iteration 1's frame has "14 findings" back to the report.
- Events: a sample iteration 1 build is 256 events and 168 console lines (was 223 and 135); iteration 2 is 264 and 164.

**Files**
- NEW backend/seedfoundry/validators/findings.py, protection.py, records.py; backend/seedfoundry/report/assemble.py
- CHANGE backend/seedfoundry/engine/script.py (real T-13 to T-20, findings, phase results, completion line, report.ready), validators/numeric.py, visual.py, latency.py, problems.py (messages, unit), report/__init__.py, main.py (report route)
- NEW backend/tests/test_findings.py, test_probes.py, test_report.py, report_fixtures.py; CHANGE backend/tests/test_engine.py
- NEW frontend/src/report.ts, stores/reports.ts, components/report/BuildReport.vue; DELETE components/build/BuildSummary.vue
- CHANGE frontend/src/views/BuildView.vue, ReviewView.vue, components/dashboard/DashboardFrame.vue ("N findings", highlight), DashboardView.vue and DashboardRenderer.vue (highlight)
- NEW frontend/tests/report.spec.ts, fixtures/reports/ (both reports and iteration 1's events, written by the backend); CHANGE frontend/tests/build-script.ts, build-view.spec.ts, dashboard.spec.ts, fake-server.ts, contrast.spec.ts
- CHANGE docs/decisions.md (D-62 to D-66; OQ-26, OQ-27; notes on D-51, D-54, D-57, D-60, OQ-21, OQ-22), docs/build-simulation.md (§2 to §6 as built, new §6.5), docs/ui-spec.md (§3 to §5 as built), docs/seed-reuse-notes.md (§2.6, §5.8 as built), docs/implementation-plan.md (M9 status, as-built note), docs/CLAUDE.md (report fixture command), docs/project-notes.md (this entry)

**Gates**
- backend: 489 passed, frontend: 398 passed (through `python run.py test`)
- `npm run build`: typecheck, build and `postbuild` network check pass
- Exit criteria:
  - The D-14 test passes: the sample's iteration 1 findings equal the catalogue exactly; iteration 2 has none; the polished dashboard gives zero problems at five drill levels (`test_findings.py`).
  - Removing any one overlay patch removes exactly its finding from the build, for all fourteen, the stylesheet's three included (`test_findings.py`).
  - Every finding shows expected and shown values from the data; the N figures equal a recount from the rows; no message has an em dash (`test_findings.py`).
  - The report has header and verdict, grouped findings, tests, gates and simulated usage for both iterations; `report.ready` agrees with it; it is the same for two runs and after a restart (`test_report.py`, `report.spec.ts`).
  - Clicking a finding opens the dashboard with its panels outlined (N-1, V-3, V-6, V-8, L-1 while waiting); "14 findings" returns to the report (`report.spec.ts`).
  - Phase results match build-simulation §2 for both iterations (`test_findings.py`); the determinism test passes.
- Checked that the tests can fail. Each change below was made, the matching tests failed, and it was reverted:
  - V-3 without the class-colour check;
  - a phase failed on any failed test;
  - the least strict policy effect winning;
  - the record contract not checking the class;
  - the verdict red for findings;
  - API calls counted as LLM calls;
  - a finding keeping only its first problem;
  - no highlight on the panels (7 tests);
  - a drill keeping the finding;
  - "N findings" off by one.
- determinism: pass | no-em-dash: pass | network: pass | contrast: pass (no new token; a new check that the accent outline is 3:1 on every surface)
- Assertions edited, recorded first in D-66:
  - `test_engine.py`: the stubbed-tests test becomes "every test runs and raises exactly the catalogue"; the boundary advisory test counts advisories only; iteration 2 reads 14 prior findings.
  - `build-script.ts`: the sample's M9 results, findings, `report.ready` and completion data; the advisory is asked for (`advisoryIn`).
  - `build-view.spec.ts`: the completion tests read the report; two selectors name the report.
  - `dashboard.spec.ts`: Back to report shows the report; View Dashboard is the report's.

**Hand checks** (terminal, through the Vite proxy at `http://127.0.0.1:5273`; `var/state.json` backed up first and restored after, same SHA-256)
- 4x: Reset, Load sample, Start Build. Iteration 1: 256 events in 18.9 s, 168 console lines, last `sim_t` 75.0.
  - T-13 and T-14 PASS. L-1 WARN in Stress & Probe; N-1 to N-5 FAIL and V-1 to V-8 WARN in Harvest Validation.
  - "Report compiled: 14 findings across 3 categories; verdict Completed with findings"; "Build completed: 15 tests passed, 5 warned, 1 failed; 14 findings, 0 boundary advisories; verdict Completed with findings".
- Every `finding.raised` line read against seed-reuse-notes §5.8's as-built table: each defect, panel and figure as the table says (V-4 on 3 panels, V-5 on 2, V-3 on 2, V-6 on 5; V-8 at 1.55:1 light and 1.44:1 dark).
- Each N figure recounted from `GET /api/datasets/primary` (13,050 rows), all equal to the findings:

  | Id | Recount | Finding |
  |---|---|---|
  | N-1 | KPI 13,050; bars at 1.2 x each product sum to 15,660 | expected 13,050, shown 15,660 |
  | N-2 | true shares sum to 100.0%; at 1.12 x each, 112.0% | 100.0%, 112.0% |
  | N-3 | recoverable classes $1,035,384; Unused and Underused $1,191,396 | $1,035,384, $1,191,396 |
  | N-4 | classes sum to 13,050; assigned 12,401 | 13,050, 12,401 |
  | N-5 | rows 13,050 + the largest (4,200) = 17,250 | 13,050, 17,250 |

- Iteration 2 by API (`POST /api/builds {"iteration": 2}`): 264 events, 0 findings, verdict Passed, 21 tests passed.
- The same build twice (Reset, Load sample, Start Build): the events are identical but for `wall_ts`, seqs, the build id and the file ids (which follow the saved counters after Reset, D-46); the reports are identical with those ids masked.
- Server restart (both processes stopped and started): `GET /api/builds/b-8/report` is byte for byte what it was before.
- The review route with `finding=V-3` is served through the proxy.
- Nothing was checked in a browser. Waiting on the stakeholder, in a browser:
  - Watch an iteration 1 build at 1x: do the findings appear in phases 9 and 10 as they are found, and does the log read matter-of-fact?
  - Read the iteration 1 report: verdict, findings with expected and shown, tests, gates, simulated usage.
  - Click each dashboard finding: is the right panel outlined, including V-3 (two panels), V-6 (five) and L-1 (while the treemap waits)?
  - Use the "14 findings" link from the dashboard back to the report.
  - Read the iteration 2 report.
  - Check both themes, and the whole report and its finding links by keyboard only.

**Decisions and questions**
- New: D-62 (T-13 and T-14 real), D-63 (findings model, statuses, phase results, messages), D-64 (the report, verdict and tone, `report.ready`), D-65 (the report on screen, finding links, highlight, "N findings"), D-66 (assertions changed)
- Opened: OQ-26 (severity scale), OQ-27 (whether a failed probe should be a finding)
- Updated: OQ-21 and OQ-22, asked again: the Build page stays on `/build/<n>` with the report above the stepper, and `/review/<n>` shows the same report
- Closed: none. OQ-19 to OQ-25 are unanswered, so their assumptions stand.

**Notes for next milestone**
- M10:
  - Embed `components/report/BuildReport.vue` in the "Feedback + Report" view with `heading-level` 3 and `:actions="false"`; it loads its own report.
  - "Changes since iteration 1" (FR-R-3) can list iteration 1's findings from its report (`GET /api/builds/<iteration 1 id>/report`, `groups`), each marked resolved when iteration 2's report has none of that id; the feedback quote comes from `observer-feedback-iteration-1.md`.
  - `DashboardView` takes `highlight` (panel ids), so the split view can outline a finding too.
  - After a change to the build, the validators or the report, rewrite the fixtures with `uv run python tests/report_fixtures.py`.
- M11: known issues on iteration 1 approval are the report's findings (`groups`, advisories apart).

### M10: Rebuild modal and iteration 2 (2026-10-04)

**What changed**
- Rebuild is real (D-67, D-70). On iteration 1's report it opens "Rebuild Seed: observer feedback": a large modal over the page with the Knowledge editor (Edit / Preview, mic) for `observer-feedback-iteration-1.md`, a view tablist (Feedback, Feedback + Report, Feedback + Dashboard), Cancel and Start Rebuild. Split views put the editor left and iteration 1's report (no actions) or dashboard right, each scrolling on its own; the embedded dashboard keeps its own drill path, so the page URL never moves, and a finding id in the embedded report shows that finding on the embedded dashboard, outlined.
- Start Rebuild is disabled, with its reason, while the feedback is empty or whitespace. Pressed, one request (`POST /api/builds` with `iteration: 2` and the feedback) saves the Misc Context file and starts iteration 2 in one state change, then `/build/2` opens. A refusal or a failed save leaves neither the file nor the build. An existing feedback file is rewritten in place. Once iteration 2 has started, iteration 1's report says it was rebuilt instead of offering Rebuild.
- Feedback routing is real (D-68, replacing D-52's stub). Segments are scored against the boundary lint's own rule sets (plus a few words for homes the lint never checks), ties go to D-36's fixed order, and each routed segment is appended verbatim under `### Observer feedback (iteration 1)` at the end of its section. The files really change as each Update sub-step plays (`intake.file_updated`), and every later sub-step reads the routed files. A segment already there is not added twice.
- Every build keeps the intake it read (`files`), so iteration 1's versions stay with build 1 (`GET /api/builds/{id}/files`).
- Iteration 2's report has "Changes since iteration 1" (D-69), assembled on the server from both builds' kept logs and the feedback build 2 kept: every iteration 1 finding resolved or open, the feedback quoted in a sanitised blockquote, and the edits the routing made.
- Prefill (Shift+F) fills the open modal with the demo feedback, served by `GET /api/demo/feedback` from `backend/seedfoundry/sample/rebuild/`. It routes 9 of 10 segments to all four files and raises no advisory.
- The Knowledge editor's toolbar and text are now `MarkdownEditor.vue`, shared by FileEditor and the modal; Knowledge looks the same.
- Events: the sample's iteration 2 with the demo feedback is 278 events and 178 console lines (was 264 and 164); iteration 1 is unchanged (256 and 168).

**Files**
- NEW backend/seedfoundry/intake/routing.py, backend/seedfoundry/sample/rebuild/observer-feedback-iteration-1.md
- CHANGE backend/seedfoundry/engine/script.py (real Route and Update sub-steps, routed files), engine/runner.py (the rebuild's single save, routed files written as beats play), state.py (`Build.files`), report/assemble.py (`changes`), main.py (`feedback` on start, `/files`, `/api/demo/feedback`), intake/boundary.py (`clean` public), sample/__init__.py (`demo_feedback`)
- NEW backend/tests/test_routing.py, test_rebuild.py; CHANGE backend/tests/test_engine.py, test_build_api.py, report_fixtures.py
- NEW frontend/src/components/rebuild/RebuildModal.vue, components/intake/MarkdownEditor.vue, stores/rebuild.ts
- CHANGE frontend/src/App.vue, builds.ts, report.ts, demo/api.ts, demo/DemoController.vue, stores/demo.ts, components/base/BaseModal.vue, components/intake/FileEditor.vue, MarkdownPreview.vue, components/report/BuildReport.vue, components/dashboard/DashboardView.vue
- NEW frontend/tests/rebuild-modal.spec.ts; CHANGE frontend/tests/fake-server.ts, build-script.ts, build-view.spec.ts, demo.spec.ts, report.spec.ts, stepper.spec.ts, fixtures/reports/ (rewritten: iteration 2 rebuilt with the demo feedback)
- CHANGE docs/decisions.md (D-67 to D-71; OQ-28 to OQ-30; notes on D-36, D-47, D-49, D-52, D-64, D-65), docs/build-simulation.md (§2, §3, §4, §9 as built), docs/ui-spec.md (§2, §3, §4, §6, §8 as built), docs/implementation-plan.md (M10 status, as-built note), docs/seed-reuse-notes.md (§6.2), docs/CLAUDE.md (report fixture command), docs/project-notes.md (this entry)

**Gates**
- backend: 528 passed, frontend: 417 passed (through `python run.py test`)
- `npm run build`: typecheck, build and `postbuild` network check pass
- Exit criteria:
  - Two-iteration flow at API level: iteration 1, the rebuild with the demo feedback, iteration 2 with zero findings and verdict Passed; its report lists all 14 iteration 1 findings as resolved and quotes the feedback; the feedback file is in Knowledge (`test_rebuild.py`).
  - Routing: each rule set sends a segment to its file and section; ties break in the fixed order (eight real ties); more matches beat the order; an unmatched segment changes no file; the same feedback gives the same edits, and routing it again adds nothing (`test_routing.py`).
  - The demo feedback updates all four files and raises no advisory; each Update line's file, section, segments and lines added match a diff of build 1's kept files against Knowledge (`test_routing.py`, `test_rebuild.py`).
  - Iteration 1's file versions are kept with build 1 and left out of the snapshot (`test_rebuild.py`).
  - Modal: Start Rebuild disabled while empty or whitespace, with its reason; the three views (tablist, keyboard, report without actions, dashboard drill with no URL change, finding to outlined panel); Cancel saves nothing and discards nothing saved; Escape returns focus; backdrop click ignored; focus trapped; Shift+F prefills only inside the modal and types in the editor; Rebuild not on iteration 2 and no shortcut reaches the modal (`rebuild-modal.spec.ts`).
  - Knowledge after a rebuild starts: the feedback file in Misc Context, read-only, a core file showing its added section (`rebuild-modal.spec.ts`).
- Checked that the tests can fail. Each change below was made, the matching tests failed, and it was reverted:
  - ties going to the last target;
  - a segment already present added again;
  - lines added off by one;
  - routed files never written to Knowledge;
  - the feedback saved in its own change before the build (the failed-save test);
  - every finding reading resolved;
  - whitespace counted as feedback;
  - a finding in the embedded report linking the page;
  - Prefill firing without the modal;
  - the embedded dashboard's drill moving the URL.
- determinism: pass (and the full two-iteration flow twice in-process: identical) | no-em-dash: pass (the demo feedback, the routed lines, the changes section) | network: pass | contrast: pass (no new token)
- Assertions edited, recorded first in D-71:
  - `test_build_api.py`: iteration 2 needs feedback (`feedback_empty` without it).
  - `test_engine.py`: the helper rebuilds with the feedback; D-52's no-routing test becomes the routing test; the no-feedback case is built as a script.
  - `demo.spec.ts`: Prefill's button says the modal must be open.
  - `build-view.spec.ts`: Rebuild opens the modal; iteration 2's feedback sub-steps show the routing's summaries.
  - `stepper.spec.ts`: the same summaries.
  - `report.spec.ts`: iteration 2 also has the changes section.

**Hand checks** (terminal, through the Vite proxy at `http://127.0.0.1:5273`; `var/state.json` backed up first and restored after, same SHA-256 `140f3633...`)
- 4x: Reset, Load sample, Start Build, then the rebuild by the modal's request with `GET /api/demo/feedback`'s text. Iteration 1 in 18.8 s; iteration 2 in 18.9 s, 278 events, 178 console lines.
- Every Apply observer feedback line read against a diff of `GET /api/builds/b-5/files` (iteration 1's kept versions) and `GET /api/intake/files`: only inserts; person.md +4 in Reasoning methods (segment 8), instrument-awareness.md +4 in Model Behaviour (segment 7), environment.md +4 in Data Layer (segment 1), +4 in User Experience (segment 6), +10 in Styling (segments 2 to 5), music.md +4 in Value Logic (segment 9); segment 10 in the feedback file only. "Intake updated: 4 files changed, fingerprint 49616b (was 6bb2d9)".
- Iteration 2: verdict Passed, 0 findings, 0 advisories, "Changes since iteration 1" with 14 resolved and 0 open, the feedback quoted. Iteration 1's report has no changes section.
- The same flow twice: events of both builds, both reports, both builds' kept files and Knowledge identical with `wall_ts`, seqs, build ids and file ids masked.
- Server restart (both processes stopped and started): both reports, build 1's files and Knowledge byte for byte as before; `/review/1` is served through the proxy.
- Nothing was checked in a browser. Waiting on the stakeholder, in a browser:
  - Open Rebuild from the iteration 1 report. Write feedback in each view: Feedback only, beside the report, beside the dashboard (drill there; the page URL should not change). Click a finding id in the report view.
  - Press Shift+F in the modal (with focus on the tabs, not the text), then Start Rebuild. Watch phase 1 route the feedback and update the four files at 1x.
  - Open Knowledge and read the added "Observer feedback (iteration 1)" sections and the feedback file.
  - Read iteration 2's report, including "Changes since iteration 1". Open its dashboard and confirm it is clean.
  - Check both themes, and the whole modal by keyboard only.

**Decisions and questions**
- New: D-67 (the rebuild's one request, kept files), D-68 (routing), D-69 ("Changes since iteration 1"), D-70 (the modal on screen, Prefill), D-71 (assertions changed)
- Opened: OQ-28 (what closing the modal keeps), OQ-29 (Prefill replaces the text), OQ-30 (the routing list in the changes section)
- Closed: none. OQ-19 to OQ-27 are unanswered, so their assumptions stand.

**Notes for next milestone**
- M11:
  - Known issues on iteration 1 approval are iteration 1's report findings (`groups`, advisories apart); iteration 2's learned rules come from `changes.findings` categories, as Synthesis already logs.
  - The Seed page's iteration history can read `changes` (findings, feedback, updates) from iteration 2's report; the feedback text is `changes.feedback.content`.
  - Generated files read the routed core files, which build 2 keeps in `files`; the observer feedback sections are part of them.
  - Approve is still the stub in `BuildReport.vue` (`APPROVE_WHY`).

### M11: Seed file generation and final page (2026-10-04)

**What changed**
- Generation is real (D-72). Synthesis writes `core.md`, `adaptation.md` and `protection.md` in full from the intake the build reads, replacing D-51's outlines, so the manifest, the upload checksums and Planting's heading summary are computed from the real files. Each file has the header block, one line on what the layer holds, and build-simulation §7's sections in order, filled by project-notes §4's mapping, which no file or screen states. Iteration 2 reads build 2's routed files, so each "Observer feedback (iteration 1)" sits in the layer its section belongs to. A mention of an intake file by name reads as the layer that holds it now ("as core.md defines them").
- Learned rules (iteration 2): one rule per class of finding iteration 1 raised, from its kept findings, each citing the findings it came from. Synthesis's line ("3 rules, one per finding class (Latency, Numeric, Visual)") and the file agree.
- Approve is real (D-73): `POST /api/seed/approve` approves the current iteration's completed build, once, with no build running. Iteration 1 cannot be approved once iteration 2 has started. A build after approval is refused, and Reset clears the approval. One new event, `seed.approved`, outside any build. Known issues are the approved build's open findings, advisories never (OQ-31): iteration 1's 14, in a Known issues section of each file and on the page.
- Downloads (D-74): each file and `license-optimization-seed.zip` from `/api/seed/...`. The zip is stored with fixed times and attributes, so the same approval gives the same bytes.
- The Seed page, `/seed` (D-75): the hero with the real approval date (OQ-33), what the Seed does, tests by phase, the iteration history with the feedback as a disclosure, known issues, and three file cards with Preview (sanitised) and Download, plus Download all (.zip). Before approval it says why it is empty and points the way. Approve on a report opens it with no confirmation (OQ-32). The journey's Seed step links once approved.
- Events and console: unchanged at 256 events and 168 lines (iteration 1), 278 and 178 (iteration 2). Only the Synthesis and Package lines read differently, and Cross-Examination's simulated token counts grew with the drafts.

**Files**
- MOVE backend/seedfoundry/generate/outline.py to generate/layers.py (the templates, rewritten)
- NEW backend/seedfoundry/package.py
- CHANGE backend/seedfoundry/engine/script.py (full drafts, Package line), state.py (`Approval.build_id`, `approved_at`), events.py (`seed.approved`), main.py (the four `/api/seed` routes), report/assemble.py and report/__init__.py (`raised` public)
- NEW backend/tests/test_seed.py, seed_fixtures.py, golden/seed/iteration-1/ and iteration-2/ (the three files each); CHANGE backend/tests/test_no_em_dash.py (generated output and the zip)
- NEW frontend/src/seed.ts, stores/seed.ts, components/seed/SeedHistory.vue, SeedFiles.vue; MOVE (removed) frontend/src/components/ScreenPlaceholder.vue, no screen uses it now; CHANGE frontend/src/views/SeedView.vue (the page, replacing the placeholder), components/report/BuildReport.vue (Approve), components/shell/JourneyIndicator.vue, events.ts, stores/lab.ts
- NEW frontend/tests/seed.spec.ts, fixtures/seed/; CHANGE frontend/tests/fake-server.ts, shell.spec.ts, build-view.spec.ts, fixtures/reports/ (rewritten)
- CHANGE docs/decisions.md (D-72 to D-76; OQ-31 to OQ-34; notes on D-10, D-44, D-51, D-65), docs/build-simulation.md (§2 to §4, §7, §9 as built), docs/ui-spec.md (§1, §3, §4, §7 as built), docs/implementation-plan.md (M11 status, as-built note), docs/CLAUDE.md (the Seed fixture command), docs/project-notes.md (this entry)

**Gates**
- backend: 562 passed, frontend: 443 passed (through `python run.py test`)
- `npm run build`: typecheck, build and `postbuild` network check pass (downloads are relative `/api` links)
- Exit criteria:
  - Golden tests for both paths. Iteration 2 approved: learned rules, one per class from the data, and no known issues. Iteration 1 approved: all 14 open findings in a Known issues section of each file and on the page, and no learned rules. Header block and §7's sections in order in every file (`test_seed.py`).
  - The no em dash test scans both paths' files, the zip's contents read back from its bytes, and the page data (`test_no_em_dash.py`).
  - Over HTTP: each file and the zip download; the zip holds exactly the three files, byte for byte; the same approval twice gives the same zip bytes, files, page (with `approved_at` set aside) and events; a build after approval is refused; Reset clears the approval; downloads and the page survive a restart (`test_seed.py`).
  - The Seed page: every §7 section for both paths, Preview sanitised (the hostile sample), the feedback disclosure expands and collapses, no intake file named on the page, the empty page says why and points the way, Approve's availability and refusals, the journey's Seed link (`seed.spec.ts`, `shell.spec.ts`).
  - FR-F-1 to FR-F-5, AC-4 and AC-5: the tests above.
- Checked that the tests can fail. Each change below was made, the matching tests failed, and it was reverted:
  - the zip's entries in reverse order;
  - the zip dated from the clock;
  - no Known issues on approval;
  - learned rules from a fixed list;
  - Reset keeping the approval;
  - iteration 1 approvable after the rebuild;
  - intake file names not rewritten;
  - an em dash in a generated rule;
  - the feedback always shown;
  - Preview without the sanitiser;
  - Approve not opening the Seed page;
  - known issues hidden on the page.
- determinism: pass (and the same approval twice: identical files, zip, page and events) | no-em-dash: pass (generated output included) | network: pass | contrast: pass (no new token)
- Assertions edited, recorded first in D-76:
  - `shell.spec.ts`: the `/seed` placeholder row becomes the Seed page test.
  - `build-view.spec.ts`: Approve approves and opens the Seed page instead of saying M11 brings it.

**Hand checks** (terminal, through the Vite proxy at `http://127.0.0.1:5273`; `var/state.json` backed up first and restored after, same SHA-256 `9e510636...`)
- 4x: Reset, Load sample, iteration 1 (18.8 s), the rebuild with `GET /api/demo/feedback`'s text, iteration 2 (18.9 s), Approve iteration 2. Downloaded the three files and the zip. The zip holds exactly the three files, byte for byte.
- Read the three files. They read as one Seed: the header block, §7's sections in order, and the feedback sections in Execution guidance, Reasoning approach, Value logic, Data sources and mappings and Presentation notes. Learned rules has Numeric, Visual and Latency, each citing its findings. No intake file is named and there is no em dash.
- Reset, then Approve iteration 1: all 14 findings, catalogue order, in the Known issues section of each file and in the page data; no Learned rules.
- The iteration 2 path run twice: the files and the zip bytes are identical. The page data differs only in build ids (the counter carries across Reset) and `approved_at`.
- Server restart (both processes stopped and started): the files, the zip and the page are byte for byte as before, `approved_at` included; `/seed` and the zip are served through the proxy.
- Nothing was checked in a browser. Waiting on the stakeholder, in a browser:
  - Approve from iteration 2's report and read the Seed page top to bottom. Expand and collapse the observer feedback. Preview and download each file, and download the zip.
  - Reset, Load sample, build iteration 1, approve it from its report, and read the known issues on the page.
  - Both themes, and the whole page by keyboard only.
  - Still pending from M9 and M10: the report and its finding links on the dashboard, and the rebuild modal (its three views, Prefill, Start Rebuild at 1x).

**Decisions and questions**
- New: D-72 (generation), D-73 (Approve), D-74 (downloads and the zip), D-75 (the Seed page and Approve on screen), D-76 (assertions changed)
- Asked and closed by the stakeholder: OQ-31 (advisories are not known issues), OQ-32 (no confirmation on Approve), OQ-33 (the real approval date, on the page only)
- Opened: OQ-34 (an iteration 2 approved with findings lists them as known issues; the sample never has any)
- OQ-19 to OQ-30 are unanswered, so their assumptions stand.

**Notes for next milestone**
- M12:
  - The demo script's end: Approve on iteration 2's report, then the Seed page and Download all (.zip). Reset clears the approval for the next rehearsal.
  - The offline check should cover the downloads: they are same-origin `/api` links.
  - Approve has no shortcut; the operator presses it on the report.

### M12: Hardening, operator guide, rehearsal (2026-10-04)

**What changed**
- `docs/operator-guide.md` covers set up once per machine, start and stop, the controls, a timed demo script (8 to 10 minutes at 1x), what to do if something goes wrong on stage, rehearsing, checks before a demo, and troubleshooting. It follows Seed v0.1's guide (seed-reuse-notes §6.3).
- The rehearsal, `npm run rehearse` (D-77), plays the whole demo in headless Chrome through the UI and the operator's shortcuts:
  - It runs against an isolated copy of the app on spare ports with a throwaway `var/`, so the presenting app and its state are never touched.
  - The network is cut off: Chrome resolves no host but 127.0.0.1, and the backend runs under a guard that refuses any other connection.
  - It checks AC-1 to AC-10 and NFR-1, NFR-3 and NFR-6 in a real browser, saves screenshots of every page in both themes, and exits non-zero on a failed check.
- The offline guard and `test_offline.py`: the whole demo runs in-process with every lookup or connection outside loopback refused, and nothing is attempted (NFR-2, AC-9).
- `vite.config.ts` reads `SEEDFOUNDRY_API_URL` for its proxy target. Only the rehearsal sets it; `python run.py` is unchanged.
- No product code changed: the rehearsal found nothing in the app to fix.

**Files**
- NEW docs/operator-guide.md
- NEW frontend/scripts/rehearse.ts; CHANGE frontend/package.json (`rehearse`), frontend/vite.config.ts (`SEEDFOUNDRY_API_URL`)
- NEW backend/tests/offline.py, offline_guard/sitecustomize.py, test_offline.py
- CHANGE docs/decisions.md (D-77), docs/implementation-plan.md (M12 status, as-built note), docs/seed-reuse-notes.md (§6.3 as built), docs/README.md and docs/CLAUDE.md (the guide, the rehearse command), docs/project-notes.md (this entry)

**Gates**
- backend: 564 passed, frontend: 443 passed (through `python run.py test`)
- `npm run build`: typecheck (the rehearsal script included), build and `postbuild` network check pass
- One earlier run of the frontend suite, right after a rehearsal ended, had 6 failures, 2 of them in `dashboard.spec.ts`, which took 47 s. They did not come back in three later runs, the full gate above included. I read them as timeouts under load and did not find their cause. Watch for them; vitest's default timeout is 5 s per test.
- The rehearsal at 1x: 30 of 30 checks passed. At 4x: 30 of 30.
- Checked that the rehearsal's checks can fail. Each fault below was planted, the matching check failed, and it was reverted:
  - focus rings removed (`base.css`): every page's keyboard check failed;
  - a stylesheet from another host in `index.html`: AC-9 failed, naming the URL;
  - a 150 ms stall on each keystroke in the editor: the 1 MB check failed (192 ms).
  - The first versions of two checks were too weak and were fixed before these runs. The keyboard walk now starts at the top of the page. The keystroke timer now starts at the key's own timestamp, so the app's handlers fall inside it.
- determinism: pass | no-em-dash: pass (the guide and the script included) | network: pass (and AC-9 below) | contrast: pass (no new token)
- Assertions edited: none.

**Acceptance criteria** (AC-1 to AC-10, the M12 exit criterion)

| AC | Verified by | Result |
|---|---|---|
| AC-1 | `test_engine.py` (75 s simulated, the 14 findings), `test_findings.py` (D-14); rehearsal at 1x | Iteration 1 in **75.5 s** by the wall clock; N-1 to L-1 exactly; 168 console lines |
| AC-2 | `test_overlay.py`, `report.spec.ts`, `dashboard.spec.ts`; rehearsal screenshots | Every finding has expected and shown. The iteration 1 dashboard shows every defect at a glance: three number formats, the off-palette treemap overflowing its card, legend shares over 100%, the red line, the serif title, the twelve-slice pie, the doubled total without $, faint text, clipped columns, the 4.5 s spinner |
| AC-3 | `test_rebuild.py`, `rebuild-modal.spec.ts`; rehearsal | Rebuild with Shift+F's text; iteration 2 in 75.7 s, Passed, 0 findings, "14 of 14 iteration 1 findings resolved.", the feedback quoted; the polished dashboard |
| AC-4 | `test_seed.py`, `seed.spec.ts`; rehearsal | The Seed page with its four sections; core.md 10,216 B, adaptation.md 8,218 B, protection.md 2,918 B, the zip 21,668 B, none with an em dash |
| AC-5 | `test_seed.py`, `seed.spec.ts`; rehearsal | Approve on iteration 1: 14 known issues on the page and in each file |
| AC-6 | `knowledge.spec.ts` (gating, import dialog, category pre-selection); rehearsal | Start Build disabled with "Missing: Person, Instrument Awareness, Environment, Music", enabled with the four |
| AC-7 | `build-view.spec.ts` (refresh), `test_persistence.py`, `test_rebuild.py` and `test_seed.py` (restart); rehearsal | A reload mid-build showed the full log so far (52 lines, 52 events held); a backend restart kept Knowledge and the same zip bytes |
| AC-8 | `test_engine.py` (two runs at different speeds and with skips), `test_rebuild.py` and `test_seed.py` (the same flow twice); rehearsal | Identical streams, reports, files and zip. Reset then Load sample gave the same Knowledge byte for byte |
| AC-9 | `test_offline.py`, `network.spec.ts`, the `postbuild` check; rehearsal | Chrome with no host resolving but 127.0.0.1: 586 requests, all to 127.0.0.1. The backend under the guard attempted nothing outside loopback |
| AC-10 | `demo.spec.ts`, `shortcuts.spec.ts`; rehearsal | Shift+O toggles; Shift+P, Shift+Enter, Shift+F and Shift+R work; a shortcut in the editor does nothing; speed 4x used for the second path |

**NFR-3 and NFR-6, measured in the real browser** (the 1x rehearsal)
- Dashboard first render, from View Dashboard to every panel drawn: iteration 1 **258 ms** (the treemap's planted wait aside), iteration 2 **183 ms**. Under 1 s.
- The console over a whole build: no task over 50 ms after the reload (Chrome's long-task threshold), so no jank.
- A 1 MB file in the editor: 22 keystrokes, the slowest **40 ms** from key to frame.
- Keyboard: Tab from the top reaches every visible control, each with a focus ring, on Knowledge (17), the Build page with the report (39), the iteration 1 dashboard (38) and the Seed page (16).

**Hand checks**
- The rehearsal ran at 4x and 1x in headless Chrome, isolated, offline. I read its screenshots: Knowledge, both reports, both dashboards, the rebuild modal, both Seed pages, and a Preview, in both themes.
- Not done, for the stakeholder:
  - **The full rehearsal with the demo script, timed, by hand** (the milestone's hand check): operator guide §4 at 1x, with a stopwatch, in your Chrome.
  - **AC-9 with the network actually off**: turn Wi-Fi or Ethernet off, launch, and run to the Seed page (operator guide §7, step 3).
  - The browser checks still open from M9 to M11 (the report's finding links, the rebuild modal's views, the Seed page). The rehearsal covers them mechanically, but a person's eye is still the test of "reads well".
- During M11's hand check I stopped the launcher, but its two children (uvicorn on 8100, Vite on 5273) kept running. That app was then used at 16:33 (iteration 2 built again as `b-9`, then approved; your browser was connected to it), so `var/state.json` now holds that state rather than the M11 backup. I left both, as they are someone's session. `run.py` should stop its children when it is ended from outside; see the notes below.

**Decisions and questions**
- New: D-77 (the offline guard, the rehearsal, the thresholds where the NFRs give none)
- Opened: none. OQ-19 to OQ-30 and OQ-34 are unanswered, so their assumptions stand.

**Notes for next milestone**
- M13 (as-built reconciliation):
  - `docs/requirements.md` NFR-3 gives no numbers for "responsive" and "without jank"; D-77 chose 100 ms and 200 ms. Record them as built or amend.
  - `run.py`: when the launcher is killed rather than sent Ctrl+C (as a tool's stop does), its children survive. Ctrl+C, the documented way, stops both. Consider a job object on Windows, or say so in the guide's troubleshooting.
  - The six transient frontend failures above, if they come back.
