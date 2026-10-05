# SeedFactory: Requirements

Status: draft v1, 2026-10-03. Amendments are added as A-n and applied inline with strike-through.

*Change request (2026-10-04, after M13):* A-7 and A-8 (D-80 to D-83) apply the stakeholder's feedback on the M13 demo; the code meets them.

*Change request CR-2 (2026-10-05):* A-9 to A-12 (D-84 to D-94) apply the stakeholder's demo feedback: SeedFoundry is renamed SeedFactory (D-87), Knowledge holds the four initiation files only, under new names that version with each iteration, and the report, console and Seed page gain the controls and wording asked for; the code meets them.

*As built (M13, 2026-10-04):* every requirement is met by the code at M13. Where the code meets one in a way its wording does not say, §11 records how; where the meaning changed, an amendment does (A-5, A-6).

## 1. Goals

| Id | Goal |
|---|---|
| G-1 | Show the full journey from knowledge files to a working, validated Seed in one sitting |
| G-2 | Make the improvement loop the centrepiece: flawed iteration, human feedback, refined iteration |
| G-3 | Prove the Seed was tested: visible phases, live logs, a report backed by real checks |
| G-4 | Feel like a lab: rich, legible build stages beyond Seed v0.1's own lifecycle |
| G-5 | Run fully offline, deterministically, with no LLM, on a presenter's laptop |
| G-6 | Leave clean seams so simulated LLM and Seed API calls can be replaced by real ones |
| G-7 | Share Seed v0.1's visual language so the two products look like one family |

## 2. Scope

| Real (actually implemented) | Simulated |
|---|---|
| Intake editor, file list, categories, import, persistence | LLM extraction, distillation, cross-examination |
| Ensemble boundary check (rule-based lint over intake text) | Seed v0.1 API, sandbox, planting, Life |
| Assay statistics (sections found, sizes, completeness) | Token counts, latencies, model names in logs |
| Validators that recompute dashboard figures from source data | Human gates inside Life (auto-resolved) |
| Generation of core.md, adaptation.md, protection.md from intake (template-based) | Effect of observer feedback on iteration 2 (scripted, D-5) |
| Report, dashboard rendering, downloads | Voice input (mic icon only, D-8) |

## 3. Out of scope

- Any real LLM or network call, API keys, accounts, auth, multi-user.
- Functional voice input or speech recognition.
- ~~More than two iterations, or~~ More than one Seed in progress at a time. Iterations go on while the observer rejects them; the demo is written for two, and iteration 3 on replays iteration 2's outcome (A-7).
- Editing the generated core/adaptation/protection files inside SeedFactory.
- Running the real Seed v0.1 code. SeedFactory simulates its API.
- Mobile layouts below 1280 px wide (desktop demo only; must not break, need not be optimised).

## 4. Functional requirements

### FR-IN: Intake

| Id | Requirement |
|---|---|
| FR-IN-1 | The intake page has a large editor (left) and a file panel (right). See `ui-spec.md` §2 |
| FR-IN-2 | Every file has a name and exactly one category: ~~Person, Instrument Awareness, Environment, Music, Misc Context~~ Identity.md, Tools_and_Skills.md, Environment.md, Value.md (the initiation files; code ids unchanged, A-9) |
| FR-IN-3 | At most one file each for ~~Person, Instrument Awareness, Environment and Music. Misc Context is unlimited.~~ Identity.md, Tools_and_Skills.md, Environment.md and Value.md; no other file can be added on Knowledge. A file added to a category takes its name: Identity.md, Tools_and_Skills.md, Environment_01.md, Value_0001.md, and each iteration whose feedback changes a numbered file steps its number (Environment_02.md) (A-9). Creating or importing a second core-category file asks to replace the existing one |
| FR-IN-4 | The editor has an Edit / Preview toggle. Edit is raw markdown with monospace font; Preview renders markdown (headings, lists, tables, code, emphasis, links) |
| FR-IN-5 | The editor shows a mic icon with a "Voice input" tooltip. It is visual only (D-8) |
| FR-IN-6 | Users can create a new file, rename, change category, and delete (with confirmation). Unsaved changes show a dot; saving is automatic after a short pause and on file switch |
| FR-IN-7 | Import accepts one or more `.md` files. A dialog asks for each file's category, pre-selected from the filename where possible (`person.md`, `player.md`, `instrument-awareness.md`, `instrument_awareness.md`, `environment.md`, `music.md`; anything else defaults to ~~Misc Context~~ an initiation file not yet added, A-9; the initiation file names are hints too). The imported file takes its category's name (A-9) |
| FR-IN-8 | A ~~core-file~~ initiation files checklist ("Initiation files") shows four slots that turn complete when that category has a non-empty file, each with the Seed file it maps to at a high level beside it, right-aligned and muted (A-9) |
| FR-IN-9 | Start Build is disabled until all four core slots are complete, with a tooltip listing what is missing |
| FR-IN-10 | Intake content persists across browser refresh and server restart |
| FR-IN-11 | Files are limited to 1 MB each and UTF-8 text; violations show a clear inline error |

### FR-B: Build

| Id | Requirement |
|---|---|
| FR-B-1 | Start Build creates a build for the current iteration and opens the build page |
| FR-B-2 | The build runs the phase catalogue in `build-simulation.md` §2 in order, with no human input |
| FR-B-3 | The build page shows each phase as a step with its sub-steps and a state: pending, active, done, done-with-findings, failed |
| FR-B-4 | A console on the right streams log lines live (format in `build-simulation.md` §4). Under its bar, always in view, a tiny note: "Language on the terminal and .md file capped to English Language. Actual messages may be unreadable." (A-11) |
| FR-B-5 | Every human gate that Seed v0.1 would raise ~~during Life~~ during the simulated Seed v0.1 run (phase 8, Seeding & Life) is auto-resolved and logged with the gate id and the knowledge used to resolve it (A-1) |
| FR-B-6 | A build takes 60 to 90 seconds at 1x speed (D-7) |
| FR-B-7 | Refreshing the page mid-build reconnects and shows the same state and full log (snapshot then replay) |
| FR-B-8 | Intake is read-only while a build runs |
| FR-B-9 | When the build completes, the report panel appears with View Dashboard, Approve and ~~Rebuild~~ Reject (A-7) |

### FR-T: Testing and validation

| Id | Requirement |
|---|---|
| FR-T-1 | The Assay phase runs the Ensemble boundary check over intake text (rules in `build-simulation.md` §6.1) and reports findings with file, line and suggested home |
| FR-T-2 | The Germination Trial includes a data-swap test: the same logic produces structurally valid output on a second, different dataset |
| FR-T-3 | Harvest Validation recomputes every dashboard figure from source data and compares it to what the dashboard payload shows (numeric reconciliation) |
| FR-T-4 | Harvest Validation runs visual QA rules over the dashboard descriptor and its applied styles (palette, chart type fitness, number formats, labels, layout, contrast) |
| FR-T-5 | Stress and Probe measures panel latency against a budget and runs protection probes |
| FR-T-6 | With the sample Seed, iteration 1 validators find exactly the 14 planted defects in `build-simulation.md` §5, no more, no fewer, and iteration 2 finds none. Boundary advisories from user-supplied files are reported separately and do not affect the verdict (D-12) |
| FR-T-7 | Each finding has an id, category (Numeric, Visual, Latency, Boundary), panel or file, expected value, shown value, severity, and the phase that found it |

### FR-R: Report

| Id | Requirement |
|---|---|
| FR-R-1 | The report shows: verdict, iteration, duration, phase results, test table, findings, auto-resolved gates, simulated usage metrics, and the Seed files' context footprint when planted: each file's share of the model's context window and their total against a 20% budget (A-8) |
| FR-R-2 | Findings are grouped by category, each with its id so the observer can cite it in feedback |
| FR-R-3 | The ~~iteration 2 report~~ report of iteration 2 on has a "Changes since iteration ~~1~~ n - 1" section listing every ~~iteration 1~~ finding of the previous iteration as resolved, and quoting the observer feedback (A-7) |
| FR-R-4 | Report actions: ~~View Dashboard~~ View Agentic Solution (opens the dashboard), Approve, ~~Rebuild. Rebuild is not shown on iteration 2 (D-6)~~ Reject, on every iteration whatever its verdict. Reject opens the rebuild modal (A-7, D-81). Then Initiate QUAD SI Review Protocol, shown only, with "* Assuming default 10 cycles" in very small text (A-11) |

### FR-D: Dashboard

| Id | Requirement |
|---|---|
| FR-D-1 | The dashboard is Seed v0.1's License Optimization dashboard, ~~using its data and figures as recorded in `seed-reuse-notes.md`~~ following its methodology and layout as recorded in `seed-reuse-notes.md` §5. The underlying data is SeedFactory's own (A-3) |
| FR-D-2 | Iteration 1 renders the "rough" variant with every planted defect from `build-simulation.md` §5 visible |
| FR-D-3 | Iteration 2 renders the "polished" variant, matching Seed v0.1's quality bar and design system |
| FR-D-4 | Both variants are descriptor-driven from the same source data. The rough variant differs only by a defect overlay (descriptor patches plus a scoped defect stylesheet) |
| FR-D-5 | The dashboard has a clear way back to the report |
| FR-D-6 | The dashboard supports drill-down in both iterations, along Seed v0.1's hierarchy: all products, vendor, product, utilisation class, seat. Clicking a chart element drills; every panel follows the current drill; a breadcrumb shows the path and Back pops one step; the deepest level lists individual seats. The drill path is in the URL, so reload and the browser's Back keep it (A-2, D-29) |

### FR-RB: Rebuild

| Id | Requirement |
|---|---|
| FR-RB-1 | ~~Rebuild~~ Reject opens a modal with the same editor as intake (Edit / Preview, mic icon) for observer feedback (A-7) |
| FR-RB-2 | The modal has a view toggle: Feedback only, Feedback + Report, Feedback + Dashboard (side by side) |
| FR-RB-3 | Start Rebuild requires non-empty feedback |
| FR-RB-4 | The feedback is saved as a Misc Context file named ~~`observer-feedback-iteration-1.md`~~ `observer-feedback-iteration-<n>.md`, n being the rejected iteration, ~~visible in the intake file list~~ kept with the builds and not listed on Knowledge (A-7, A-9) |
| FR-RB-5 | Start Rebuild starts ~~iteration 2~~ iteration n + 1 from phase 1 with all original intake plus the feedback file, and opens the build page. Iteration 3 on replays iteration 2's outcome: the polished dashboard and no findings (A-7) |
| FR-RB-6 | Iteration 2 (and every later iteration, A-7) logs show the feedback being ingested and acted on (scripted, D-5), including how it updated the four Ensemble files (FR-RB-7, A-4) |
| FR-RB-7 | Before iteration 2 rebuilds, the observer feedback updates the four core files. The feedback is split into segments (paragraphs and list items); each segment is routed to the one Ensemble file, and section, its content belongs in; routed segments are appended verbatim to that file under an "Observer feedback (iteration 1)" subsection; a segment that fits no core file stays in the feedback file only. The routing is shown as an LLM decision (simulated) but is deterministic. The updated files are what iteration 2 builds from, and the Knowledge page shows them (A-4, D-36) |
| FR-RB-8 | On the build page in iteration 2 (and every later iteration, A-7), the feedback routing and each file update are visible as sub-steps of phase 1, as log lines naming the file, the section and the lines added (A-4), and in a panel showing which segments went into each of the four files (D-83) |

### FR-F: Final page

| Id | Requirement |
|---|---|
| FR-F-1 | Approve (either iteration) opens the final page |
| FR-F-2 | The final page shows: Seed name, what it does (from the Music purpose), tests conducted with results, iteration history, and known issues |
| FR-F-3 | Downloads: `core.md`, `adaptation.md`, `protection.md`, each individually and as one zip. The zip is a "download" link beside a "Secure and Lock in Secure Repository" button, which is shown only (A-10) |
| FR-F-4 | ~~If iteration 1 was approved, every open finding is listed as a known issue on the page and in a "Known issues" section of each generated file (D-10)~~ If the approved build has open findings (an iteration 1 approval always does; an iteration 2 approval only if it still has some), every open finding is listed as a known issue on the page and in a "Known issues" section of each generated file. Boundary advisories are not known issues (D-10, D-73, OQ-31, OQ-34, A-5) |
| FR-F-5 | Generated files contain no em dashes and follow the structure in `build-simulation.md` §7 |

### FR-DC: Demo controller

| Id | Requirement |
|---|---|
| FR-DC-1 | A hidden demo controller panel toggles with a Shift-based shortcut, following Seed v0.1's operator pattern. Shortcuts are ignored while focus is in a text field |
| FR-DC-2 | Actions: Load sample Seed, Clear intake, Speed (1x, 2x, 4x), Skip to end of phase, Skip to end of build, Prefill rebuild feedback, Reset to start, Toggle light/dark |
| FR-DC-3 | The sample Seed is a complete, Ensemble-clean set of four License Optimization files written for this project (content guidance in `build-simulation.md` §8), named as Knowledge names them, with no Misc Context file (A-9) |
| FR-DC-4 | Demo controller actions never change determinism: speed and skip change pacing only, not content |

## 5. Naming

| Code term | Screen term |
|---|---|
| `intake` | Knowledge |
| `person`, `instrument_awareness`, `environment`, `music` (categories) | Identity.md, Tools_and_Skills.md, Environment.md, Value.md (A-9) |
| core files | Initiation files (A-9) |
| `build` | Build |
| `iteration` | Iteration |
| `finding` | Finding |
| `report` | Build Report |
| `seed_package` | Seed |
| `observer_feedback` | Observer feedback |
| `rebuild` (the report action) | Reject (the modal's own button stays Start Rebuild, D-81) |
| Seed v0.1 terms | As in `seed_docs` (INIT = Planting, RUNTIME = Life, CLOSING_SEEDING = Cleanup) |

## 6. Non-functional requirements

| Id | Area | Requirement |
|---|---|---|
| NFR-1 | Determinism | Same intake + same actions = identical event stream (ignoring `wall_ts`), report, dashboard payload and generated files. Covered by a test |
| NFR-2 | Offline | Works with the network disabled. No runtime fetches outside localhost |
| NFR-3 | Performance | ~~Intake editor stays responsive with a 1 MB file. Console handles a full build's log without jank. Dashboard first render under 1 s, except the deliberately slow panel in iteration 1~~ Intake editor stays responsive with a 1 MB file: every keystroke is drawn within 100 ms of its key. Console handles a full build's log without jank: no main-thread task over 200 ms while it streams a whole build. Dashboard first render under 1 s, from View Dashboard to every panel drawn, except the deliberately slow panel in iteration 1 (A-6) |
| NFR-4 | Architecture | State is the single source of truth on the server; event log + SSE with snapshot-then-replay; `LLMClient` and `SeedClient` interfaces with simulated implementations; descriptor-driven dashboard |
| NFR-5 | Visual | SeedFactory's own UI follows ~~Seed v0.1's design system (tokens, type, colour meaning, contrast)~~ the ValueWise SI house style (`valuewise-style.md`: palette, data scale, type, flat surfaces), with Seed v0.1's token names, colour meaning and contrast test (A-13). Only the iteration 1 dashboard breaks it, and only through the scoped defect overlay |
| NFR-6 | Accessibility | WCAG AA contrast for SeedFactory's own UI in both themes (test). Keyboard reachable controls |
| NFR-7 | Delivery | One command to launch both processes, with a Windows fallback like Seed v0.1's `run.ps1`. Operator guide with a timed demo script |
| NFR-8 | Writing | No em dashes in any UI text, log line, report or generated file. Enforced by a test |

## 7. Acceptance criteria

| Id | Criterion |
|---|---|
| AC-1 | From a fresh start: Load sample Seed, Start Build, iteration 1 completes in 60 to 90 s with findings matching the catalogue exactly |
| AC-2 | The iteration 1 dashboard visibly shows every planted defect; the report lists each one with expected vs shown |
| AC-3 | Rebuild with feedback, iteration 2 completes with zero findings, the polished dashboard matches Seed v0.1, and the report shows all iteration 1 findings resolved |
| AC-4 | Approve on iteration 2 shows the final page; the three files and the zip download and contain no em dashes |
| AC-5 | Approve on iteration 1 shows the final page with known issues listed on the page and in each file |
| AC-6 | Start Build stays disabled until the four core files exist; import asks for category and pre-selects it |
| AC-7 | Refresh mid-build resumes with full log; server restart keeps intake |
| AC-8 | Two complete runs with the same inputs produce identical event streams |
| AC-9 | The app runs with the network disabled |
| AC-10 | The demo controller toggles with its shortcut, is ignored in text fields, and every action works |

## 8. Assumptions

- Presented on a single desktop machine, Chrome, 1440 to 1920 px wide.
- One person uses it at a time.

## 9. What we take from Seed v0.1

Recorded in detail in `seed-reuse-notes.md` (written in M0).

| Take | Do not take |
|---|---|
| Design system: tokens, type, colour meaning, contrast test | ACME environment specifics beyond the License Optimization data |
| Architecture patterns: state snapshot, event log + SSE, EventSource seam, beat engine with weights, descriptor-driven dashboards, policy evaluation | Seed v0.1 rule ids as SeedFactory ids |
| Lifecycle names and order for the Planting, Life and Cleanup phases | The growth tree |
| Human gate ids and types (to auto-resolve them ~~in Life~~ in phase 8, Seeding & Life, A-1) | Seed/Life naming for SeedFactory's own screens |
| License Optimization dashboard: panels, ~~data, figures~~ methodology and layout; the data is SeedFactory's own (A-3) | |
| Operator pattern: Shift shortcuts, ignored in text fields, demo script, rehearsal tools | |
| Process: requirements, decisions, milestone plan, build log, amendments | |

## 10. Amendments

| Id | Date | Amends | Change | Ruling |
|---|---|---|---|---|
| A-1 | 2026-10-03 | FR-B-5 | Gates are auto-resolved during the simulated Seed v0.1 run in phase 8, not "during Life": Seed v0.1 raises no gate in Life | D-26 (OQ-11) |
| A-2 | 2026-10-03 | FR-D (new FR-D-6) | The dashboard supports drill-down along Seed v0.1's hierarchy | D-29 (OQ-14) |
| A-3 | 2026-10-03 | FR-D-1 | The dashboard follows Seed v0.1's methodology and layout; its data is SeedFactory's own, not Seed v0.1's figures | D-30 |
| A-4 | 2026-10-03 | FR-RB-6; new FR-RB-7, FR-RB-8 | Iteration 2 first routes the observer feedback into the four Ensemble files and updates them, visibly, then rebuilds from them | D-36 |
| A-5 | 2026-10-04 | FR-F-4 | Known issues are the approved build's open findings, whichever iteration is approved, not only an iteration 1 approval; advisories are never known issues. The sample's iteration 2 has none, so the demo is unchanged | D-73 (OQ-31, OQ-34, stakeholder) |
| A-6 | 2026-10-04 | NFR-3 | The three performance requirements get the thresholds the rehearsal measures: 100 ms from a key to its frame, no task over 200 ms while the console streams, 1 s from View Dashboard to every panel drawn | D-77 (stakeholder, M13) |
| A-7 | 2026-10-04 | §3, FR-B-9, FR-R-3, FR-R-4, FR-RB-1, FR-RB-4 to FR-RB-6, FR-RB-8 | Every report has Reject (Rebuild renamed) and Approve, whatever its verdict; rejecting iteration n starts iteration n + 1 from its feedback, with no limit; iteration 3 on routes its feedback as iteration 2 did and replays iteration 2's outcome. No iteration total is shown | D-80, D-81 (stakeholder, after M13) |
| A-8 | 2026-10-04 | FR-R-1 | The report shows the Seed files' context footprint when planted, against a 20% budget | D-82 (stakeholder, after M13) |
| A-9 | 2026-10-05 | FR-IN-2, FR-IN-3, FR-IN-7, FR-IN-8, FR-RB-4, FR-DC-3, §5 | Knowledge holds the four initiation files only, named Identity.md, Tools_and_Skills.md, Environment.md and Value.md everywhere; Misc Context is not offered and the feedback file is not listed; an added file takes its category's name, and numbered names step with each iteration that changes them; the checklist shows each file's high-level Seed file | D-84, D-85, D-86 (stakeholder, CR-2) |
| A-10 | 2026-10-05 | FR-F-3 | The zip downloads from a "download" link beside a "Secure and Lock in Secure Repository" button, which does nothing | D-93 (stakeholder, CR-2) |
| A-11 | 2026-10-05 | FR-B-4, FR-R-1, FR-R-4 | The console's language note; View Dashboard reads View Agentic Solution; Initiate QUAD SI Review Protocol, shown only, with its footnote; the footprint's window note names the one-thread assumption | D-89, D-91, D-92, D-94 (stakeholder, CR-2) |
| A-12 | 2026-10-05 | §5, ui-spec.md | An iteration rebuilt from a rejection carries a "Human" tag wherever the screen names it | D-90 (stakeholder, CR-2) |
| A-13 | 2026-10-05 | NFR-5, FR-IN-4 | The UI follows the ValueWise SI house style v3: navy, white and greys, the data scale only for a status, gold for the one headline figure, link blue only on links, flat and square, IBM Plex Sans at a screen scale, IBM Plex Mono for code (the editor's raw markdown stays monospace), dark by default. Where a guide colour fails WCAG AA (NFR-6), contrast wins | D-96 to D-101 (stakeholder, CR-3) |

## 11. As built (M13)

Where the code meets a requirement in a way its wording does not say. None of these changes what a requirement means; those that did became amendments (§10).

| Id | As built | Ruling |
|---|---|---|
| §2 Scope | The feedback routing into the four core files is real and deterministic (A-4); what iteration 2 fixes is still scripted. Voice input is the mic icon and its tooltip only | D-5, D-36, D-68, D-8a |
| FR-IN-6 | Autosave runs 800 ms after the last keystroke, and at once on a file switch, on leaving Knowledge and before Start Build. Delete, Clear Knowledge and Reset ask first | D-41, D-47 |
| FR-IN-8, FR-IN-9 | A file of only whitespace counts as missing. The checklist follows what the editor shows, saved or not. Start Build's tooltip reads "Missing: ..."; the disabled button stays focusable so the tooltip can be reached from the keyboard | D-42 (a), (c) |
| FR-IN-11 | 1 MB is 1,048,576 bytes of UTF-8. A refused file shows the server's message as written (too large, not UTF-8 text, not a `.md` name) | D-34 |
| FR-B-3 | A phase is pending, active, done, or stopped (an interrupted build). A done phase's chip carries its result: Passed, Findings: n, Failed: T-nn, or Incomplete: n of m not run. "Done-with-findings" is a done phase with a Findings chip | D-54 (c) |
| FR-B-6 | Every build is 75.0 s of simulated time. Speed and skip change only how fast it plays | D-48 |
| FR-B-9 | The page stays on `/build/<n>`: the report appears above the collapsed stepper, with its actions. `/review/<n>` shows the same report, and the dashboard's Back to report returns there | D-65 (OQ-21, OQ-22) |
| FR-T-5 | A failed protection probe (T-13) or an accepted malformed input (T-14) is a failed test, not a finding | D-62 (OQ-27) |
| FR-T-7 | Severity is high (Numeric), medium (Visual, Latency) or advisory (Boundary). A problem no catalogue entry owns still becomes a finding, with an id such as N-X1 | D-63 (OQ-26) |
| FR-R-3 | Each iteration 1 finding is listed as resolved or open, measured against iteration 2's report rather than asserted. The section also lists the files and sections the feedback updated | D-69, D-70 (OQ-30) |
| FR-R-4 | ~~Rebuild is also withdrawn from iteration 1's report once iteration 2 has started.~~ Reject stays on a superseded report, unavailable, and says the next iteration was rebuilt from it (D-81). Once a Seed is approved, every report says so in place of Approve | D-67, D-75, D-81 |
| FR-F-1 | Iteration 1 cannot be approved once iteration 2 has started; Reset is the way back. Approve asks no confirmation | D-73, D-75 (OQ-32) |
| FR-F-2 | The date is the approval's real date, on the page only; every file and compared value stays deterministic | D-73 (OQ-33) |
| FR-DC-1 | Shift+O. Shortcuts are also ignored with Ctrl, Alt or Meta held, on a key repeat, in a modal they do not belong to, and Shift+Enter on a focused button | D-47 |
| FR-DC-2 | Clear intake is "Clear Knowledge" on screen (§5). The panel also offers Start Build (Shift+Enter). Speed is kept by the server and survives Reset | D-47, D-48 |
| NFR-1 | Also the Seed page's data (all but the approval date) and the zip's bytes | D-73, D-74 |
| NFR-2 | Checked three ways: the backend under a guard that refuses any connection outside loopback (`test_offline.py`), the `postbuild` scan of `dist/`, and the rehearsal's Chrome that resolves no host but 127.0.0.1 | D-38, D-77 |
| NFR-6 | Contrast is a test over `tokens.css` in both themes; keyboard reach and focus rings are checked in a real browser by the rehearsal | D-38, D-77 |
| NFR-7 | `python run.py`, or `run.ps1` where uv is blocked. On Windows the launcher's children also end when the launcher is ended from outside | D-23, D-25, D-78 |
