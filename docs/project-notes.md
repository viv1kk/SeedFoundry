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
