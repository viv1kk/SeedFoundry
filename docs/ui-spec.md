# SeedFoundry: UI spec

The four screens, the rebuild modal and the demo controller. This describes intent and layout; exact visuals come from Seed v0.1's design system (`seed_docs/design-system.md`) and are recorded in `seed-reuse-notes.md`. Claude Code may improve layout details for cohesion as long as every requirement in `requirements.md` holds.

## 1. App shell

- Top bar: SeedFoundry wordmark (left), journey indicator (centre): **Knowledge → Build → Review → Seed**, iteration badge ("Iteration 1 of 2") when a build exists, theme toggle (right).
- The journey indicator shows where you are; earlier steps are clickable when it makes sense (e.g. back to Knowledge to read files, which are read-only during a build).
- Routes (suggested): `/knowledge`, `/build/:iteration`, `/review/:iteration` (report), ~~`/review/:iteration/dashboard`~~ `/review/:iteration?dashboard=license-optimization&drill=...` (dashboard over the report, OQ-4 closed in M0; `drill` carries the drill path, D-29), `/seed`. Follow Seed v0.1's routing and dashboard-view pattern where it applies (OQ-4).

*As built (M7, D-59):* the dashboard is `/review/<n>?dashboard=license-optimization`, with `&drill=<path>` once drilled: steps joined by `/`, a step's level ids by `.` (`drill=microsoft.microsoft-365-e3.unused`). It opens only when the iteration has a completed build. Back to report opens `/review/<n>`.

## 2. Knowledge (intake) page

```
+--------------------------------------------------------------+---------------------------+
| [ Name: music.md            ] [ Category: Music      v ]     |  CORE FILES               |
| [Edit | Preview]                                 [mic] [...] |  [x] Person               |
|--------------------------------------------------------------|  [x] Instrument Awareness |
|                                                              |  [ ] Environment          |
|                                                              |  [x] Music                |
|                   large markdown editor                      |  [ Start Build ] (disabled)|
|                                                              |---------------------------|
|                                                              |  FILES        [+ New] [Import]
|                                                              |  Person                   |
|                                                              |    person.md            * |
|                                                              |  Instrument Awareness     |
|                                                              |    instrument-awareness.md|
|                                                              |  Music                    |
|                                                              |    music.md               |
|                                                              |  Misc Context             |
|                                                              |    vendor-notes.md        |
+--------------------------------------------------------------+---------------------------+
```

- **Editor (left, ~70% width):** name field and category picker above it. Toolbar: Edit / Preview segmented toggle, mic icon (tooltip "Voice input", no action, D-8), overflow menu (Rename, Change category, Delete). Edit mode uses JetBrains Mono; Preview uses the body type and renders tables.
- **File panel (right, ~30%):** core checklist with Start Build at the top; below it the file list grouped by category in Ensemble order (Person, Instrument Awareness, Environment, Music, Misc Context). Selected file highlighted. Unsaved changes dot. Empty categories show a muted "Add file" link.
- **Empty state:** when there are no files, the editor area shows a short explainer of the four Ensemble files (one line each) and two actions: New file, Import.
- **Import dialog:** one row per selected file: filename, category dropdown (pre-selected per FR-IN-7), and a "Replaces existing person.md" warning when relevant. Confirm / Cancel.
- **Start Build:** disabled until all four core slots are complete; tooltip lists what is missing.
- During a build the page is read-only, with a banner linking to the running build.
- After a rebuild starts, the four core files show the feedback added to them under `### Observer feedback (iteration 1)` in the sections it was routed to (FR-RB-7).

*As built (M3):* the name field saves on Enter or when it loses focus, and Escape puts it back; the category picker is a menu button, not a select; Rename and Change category in the overflow menu focus those two controls (D-42). Preview shows raw HTML as text, an image as an "Image" label with its alt text and address, and a link as link-styled text followed by its address; nothing in Preview loads or navigates (D-40). The selected file is in the URL (`/knowledge?file=f-3`). The file panel shows Core files (checklist, Start Build, a status line under it), then Files with New and Import. New file starts on the first empty core slot with that slot's usual name (`person.md`). Start Build's tooltip reads "Missing: ..."; in M3 the enabled button saves every draft and says builds arrive in M5 (D-42). The import dialog blocks Import while two files are set to the same core category. The empty state lists the four core files with the server's one-line descriptions, then the Misc Context line. The read-only banner reads "A build is running. Knowledge files are read-only until it finishes." with "Go to the build".

## 3. Build page

```
+------------------------------------------+-----------------------------------+
| Iteration 1 of 2         Elapsed 00:41   |  CONSOLE            [filter v] [||]|
| ======================------------ 58%   |  00:38.2 LLM   distil music.md ... |
|                                          |  00:38.9 INFO  extracted 14 rules  |
|  (v) 1 Assay                             |  00:39.4 TEST  boundary check: 0   |
|  (v) 2 Distillation                      |  00:40.1 API   POST /seeds ...     |
|  (v) 3 Synthesis                         |  00:40.6 INFO  sandbox sbx-7f3a up |
|  (v) 4 Cross-Examination                 |  ...                               |
|  (v) 5 Germination Trial                 |                                    |
|  (*) 6 Containment                       |                                    |
|        - Seed API handshake       done   |                                    |
|        - Provision sandbox        active |                                    |
|        - Upload seed files        pending|                                    |
|  ( ) 7 Planting                          |                                    |
|  ...                                     |                                    |
+------------------------------------------+-----------------------------------+
```

- **Left (~55%):** header with iteration badge, elapsed time, overall progress. Vertical stepper of the 11 phases. The active phase is expanded to show its sub-steps; completed phases collapse to one line with duration and a result chip (Passed, Findings: 3). Click any completed phase to expand it.
- State shown by weight and colour, not motion, per Seed v0.1 ("weight not motion shows state"). A restrained progress animation on the active sub-step is fine.
- **Right (~45%): console.** Monospace, dark surface in both themes, auto-scroll with a pause control, level filter (All, LLM, API, TEST, WARN, FAIL). Lines are colour-coded by level using status tokens; red only for FAIL.
- **Iteration 2 (FR-RB-8, D-36):** phase 1 opens with "Apply observer feedback": a routing sub-step, then one sub-step per core file (person.md, instrument-awareness.md, environment.md, music.md), each showing the section it changed and the lines added, or "no change". The console shows the matching log lines.
- **On completion:** the stepper is replaced (or overlaid) by the report panel (§4). The console stays available, collapsible.

*As built (M5):* the page is still a placeholder until M6, with one live line under its heading: "Build running: phase 3 of 11, Synthesis. The phase stepper and console arrive in M6.", "Build completed. ... The report arrives in M9.", "This build stopped before it finished. Start it again from Knowledge." or "No build for this iteration yet." (OQ-18). Start Build and Shift+Enter open `/build/<iteration>`. Each build record carries its `plan` (phases, sub-steps and tests for that iteration), so M6's stepper can show pending phases from the start (D-49).

*As built (M6, D-54):* the M5 placeholder is gone. **Left:** a header (iteration chip, the Seed name, Elapsed `mm:ss`, a progress bar with its percentage, and a status line such as "Phase 6 of 11: Containment"), then the stepper of all 11 phases from the build's plan. Elapsed and progress are simulated time from `sim_t`, like the console's stamps, so they read the same at any speed and end at 01:15 (OQ-20); progress is `sim_t` over the record's `sim_seconds`. Phase marks: a hollow ring when pending; accent, bold, on the raised surface when active; filled green Passed, amber "Findings: n", red "Failed: T-nn"; a neutral ring with a neutral "Incomplete: n of m not run" chip for a phase with a test not yet run (D-51), so it reads as neither a pass nor a fault. A finished phase is a button (click, Enter or Space) showing its simulated duration and chip; it opens on its sub-steps, which read pending, active, or the `step.completed` summary. In iteration 2 the five feedback sub-steps sit first in Assay under an "Apply observer feedback" label, each ending with its summary ("no change" until M10). Nothing animates. **Right:** the console, `mm:ss.s  LEVEL  message`, one line per build event except `step.started` and `step.completed` (the stepper shows those): 132 lines for the sample's iteration 1. Filter buttons All, LLM, API, TEST (which includes PASS), WARN, FAIL; INFO shows only under All. Pause, or scrolling up, stops it following and says how many lines are below; Resume jumps to the latest. The log area takes keyboard focus for scrolling. **Refresh:** the page loads the build's events, follows the stream, and keeps both by seq, so nothing is missing or doubled; until the first load it says "Loading the build log". **On completion (OQ-21):** until M9 a "Build completed" summary sits above the collapsed stepper: duration, phases, tests, findings, boundary advisories, gates, and "The build report, with its verdict, findings and tests, arrives in M9." Its footer has View Dashboard, Rebuild (iteration 1 only) and Approve. Each is present but not yet available, and pressing it says which milestone brings it. The console gains Hide, and "Show console" brings it back. *M7 (D-59, OQ-23):* View Dashboard is available and opens `/review/<n>?dashboard=license-optimization`; Rebuild and Approve still say M10 and M11. The page stays on `/build/<n>`. *M9 (D-65, OQ-21):* the summary is gone: on completion the build report (§4) sits above the collapsed stepper, with its actions; the page stays on `/build/<n>` until OQ-21 is answered. The stepper's chips read "Findings: 1" (Stress & Probe) and "Findings: 13" (Harvest Validation) for the sample's iteration 1, and the console shows each finding as it is found (WARN, or FAIL for a numeric one). **Other states:** no build: "No build for iteration 1 yet. Start Build is on the Knowledge page once the four core files are in." (Go to Knowledge), or for iteration 2 "Iteration 2 starts when you rebuild from iteration 1's report." (Go to iteration 1). An interrupted build shows a banner, "This build stopped before it finished." with the server's reason and Go to Knowledge; its phase reads Stopped, and earlier phases whose events a restart lost read "Result not kept".

## 4. Review: report

- **Header:** verdict chip (iteration 1: "Completed with findings"; iteration 2: "Passed"), iteration, total duration, counts (phases, tests, findings).
- **Findings:** grouped Numeric, Visual, Latency, Boundary. Each row: id, panel or file, expected, shown, severity, found in phase. Clicking a dashboard finding opens the dashboard with that panel highlighted.
- **Tests:** table of every test run (id, phase, name, result).
- **Auto-resolved gates:** each Seed v0.1 human gate with how it was resolved.
- **Simulated usage:** LLM calls, tokens in/out, API calls, sandbox time. Label clearly as simulated in small text.
- **Iteration 2 only:** "Changes since iteration 1" section: each previous finding marked resolved, plus the observer feedback quoted in a blockquote.
- **Actions (sticky footer):** View Dashboard (secondary), Rebuild (secondary, iteration 1 only), Approve (primary).

*As built (M7, OQ-22):* the report is M9's. Until then `/review/<n>` is a stand-in: "Review, iteration <n>", then for a completed build "The build report, with its verdict, findings and tests, arrives in M9. Until then the build's summary is on its Build page." with View Dashboard and "Go to the build summary". Without a completed build it says "No build for iteration <n> yet, so there is nothing to review." (Go to Knowledge, or Go to iteration 1), "Iteration <n> is still building. Its report and dashboard open here when it completes." (Go to the build), or "This build stopped before it finished, so it has no report or dashboard." (Go to Knowledge).

*As built (M9, D-64, D-65):* the stand-in is gone. The report is `components/report/BuildReport.vue`, the same on the Build page and on `/review/<n>` (under "Review, iteration <n>" and a "Go to the build" link), loaded once per build from `GET /api/builds/{id}/report`, and embeddable (heading level and actions are props) for M10's split view. **Header:** "Build Report", the verdict chip (Completed with findings in the warning colour, Passed positive, Failed negative), then Iteration ("1 of 2"), Duration ("01:15 simulated"), Phases ("11, 2 with findings"), Tests ("21: 15 passed, 5 warned, 1 failed"), Findings, Boundary advisories, Gates auto-resolved. **Findings:** a group each for Numeric, Visual, Latency and Boundary, with its count; an empty group says "None."; Boundary says advisories never count against the verdict. Each group is a table (caption, column headers): Finding (the id, then its message), Panel (or File for an advisory), Expected, Shown, Severity (High red, Medium amber, Advisory neutral) and Found in (the phase). A dashboard finding's id is a link, "N-1: show on the dashboard" to a screen reader, to `/review/<n>?dashboard=license-optimization&finding=N-1`. **Tests:** every test, with its phase, name, result chip (Passed, Warned, Failed, Not run) and detail. **Auto-resolved gates:** id, kind and stage, the resolution, and its basis. **Simulated usage:** LLM calls, tokens in, tokens out, API calls, sandbox time, and "Simulated: no model, Seed API or sandbox was called." in small text. **Actions** (a sticky footer): View Dashboard; Rebuild (iteration 1 only) and Approve still say M10 and M11. "Changes since iteration 1" is M10's.

## 5. Review: dashboard

- Iteration 2: Seed v0.1's License Optimization dashboard as recorded in `seed-reuse-notes.md`, polished.
- Iteration 1: same dashboard with the defect overlay (see `build-simulation.md` §5). It should look clearly unfinished at a glance, not subtly off.
- A thin SeedFoundry frame around it: "Back to report", iteration badge, and (iteration 1) a small "N findings" link back to the report.
- Title on screen: **License Optimization** (D-27).
- **Drill-down (FR-D-6, D-29), both iterations:** a drill bar above the bands with Back and a breadcrumb (All products › vendor › product › class). Clicking a treemap cell or a bar drills; every panel follows the drill; the deepest level is the Seats table for that selection. The browser's Back pops one step, and reload keeps the path. A treemap leaf drills several levels in one click and its crumb names each level, as in Seed v0.1. In iteration 1 the defect overlay stays applied at every level.

*As built (M7, D-56, D-59):* **Frame:** "Back to report" (a link to `/review/<n>`) and the iteration badge on one line; for iteration 1, until M8, "Iteration 1's defect overlay arrives in M8, so until then this is the polished dashboard." (OQ-23). No "N findings" link until M9. **Header:** "License Optimization", and under it the source: "Primary estate, 13,050 seats; monthly usage Oct 2025 to Sep 2026, snapshot 2026-09-30". **Drill bar:** Back (disabled at All products) and the breadcrumb, crumbs separated by ›, earlier crumbs are buttons, the last is where you are; a treemap leaf's crumb reads "Microsoft › Microsoft 365 E3 › Unused". **Bands:** the KPI row; the treemap across the full width with the class legend under it (label, share, count); the three charts on one row; Optimisation candidates; Seats. **Drill:** a treemap cell (vendor, product, or a class leaf, which drills all its levels in one step), a bar of either per-product chart, or a product name in the candidates table. Every panel follows. The deepest level is a product's class, where the Seats table lists those seats. The drill bar's Back steps back in history when the previous entry is the parent level, and otherwise opens the parent; the browser's Back pops one step; reload keeps the path and its crumbs. A path the data does not have reopens at All products with "The drill path in the address is not in the data, so the dashboard opened at All products." **Seats table:** 25 rows a page, "Seats 1 to 25 of 13,050, page 1 of 522" between First, Previous and Next, Last; every column header sorts (ascending, then descending), and page and sort are not in the URL. **Keyboard:** every control above is a button; each chart takes focus, the arrow keys, Home and End choose a drill target, a line under the chart reads it out ("Microsoft 365 E3: 4,200. Press Enter to drill in."), a bar's tooltip shows it, and Enter or Space drills. **Charts** repaint on a theme switch and once the fonts have loaded; colours come from the chart tokens only. The dashboard component is embeddable for M10's split view (`components/dashboard/DashboardView.vue`).

*As built (M8, D-60, OQ-23):* the frame's iteration 1 line is gone. Iteration 1 shows the rough dashboard: the same frame, header and drill bar, with the defect overlay inside the dashboard only (its root carries the class `defects-overlay`; the frame and the top bar stay on the design system). On screen: KPIs in three number formats; the Recoverable KPI off the cost by product; uneven KPI gutters and one card dropped off the row; the treemap behind a spinner ("Loading Seats by vendor and product") for 4.5 s, then wider than its card, Unused in an off-palette blue, legend shares summing to about 112%; the per-product bars inflated, Active in teal and no axis names; the monthly trend with a red In use line, no axis names and a serif title; recoverable cost as a pie of twelve slices; the candidates' total row too large, recoverable figures without "$", the caption and Withheld cells in a faint grey; the Seats footer total wrong and its last two columns clipped. Every other panel is usable while the treemap waits; its chart reads "Loading Seats by vendor and product." to the keyboard and drills nothing until drawn. The overlay holds at every drill level, with the exceptions in `seed-reuse-notes.md` §5.8; the treemap waits again on each drill and on reload, not on paging or sorting (OQ-25). Iteration 2 is unchanged. Drill, crumbs, sort and pagination work by keyboard on both.

*As built (M9, D-65):* **"N findings":** iteration 1's frame has "14 findings" beside the iteration badge, a link to `/review/1`; N is the report's count, so iteration 2 has none. **Highlight:** a finding opened from the report carries `finding=<id>` in the URL. Every panel it names is outlined in the accent (2 px, offset 3 px) on its own card, so a card the overlay moved keeps its outline; V-3 outlines the treemap and the product chart, V-6 the Assigned, Active and Unused or underused cards, the treemap and Seats; L-1 outlines the treemap's card while its spinner waits. A line under the frame's bar says "Showing V-3 on Seats by vendor and product and Entitled, assigned and active by product." with the finding's message and Clear highlight; it takes focus, and the first panel scrolls into view. A reload keeps the highlight; a drill, a crumb or Back drops it. An id the report does not have says "No finding V-99 in this build's report, so nothing is highlighted." The outline is SeedFoundry's own style (the renderer's), never in `defects.css`, and adds no token.

## 6. Rebuild modal

- Large modal (about 90% of viewport). Title: "Rebuild Seed: observer feedback".
- Body: the intake editor component (Edit / Preview, mic icon), pre-titled `observer-feedback-iteration-1.md`, placeholder text prompting for data, correctness, style, chart choice, latency, and any other observation, citing finding ids where possible.
- View toggle in the modal header: **Feedback | Feedback + Report | Feedback + Dashboard**. Split views place the editor left and the chosen reference right, each scrollable independently.
- Footer: Cancel, **Start Rebuild** (primary, disabled while feedback is empty).

## 7. Seed (final) page

- Hero: Seed name, "Approved" chip, approved iteration, date.
- **What this Seed does:** short summary built from the Music file's Purpose section (falls back to the first paragraph of music.md).
- **Tests conducted:** compact table by phase with results.
- **Iteration history:** timeline: Iteration 1 (n findings) → Observer feedback (expandable) → Iteration 2 (passed). If approved at iteration 1, the timeline ends there.
- **Known issues:** only when approved at iteration 1.
- **Seed files:** three cards (core.md, adaptation.md, protection.md), each with a short description, size, Preview and Download; plus Download all (.zip).
- Do not describe which Ensemble file maps to which output file (D-9).

## 8. Demo controller

- Hidden by default. Toggled with a Shift-based shortcut (choose to match Seed v0.1's operator conventions; record in `seed-reuse-notes.md`). Ignored while focus is in an input, textarea or the editor.
- Small floating panel, bottom right, clearly an operator tool (muted styling, "Demo" label).
- Actions: Load sample Seed, Clear intake (with confirm), Speed 1x / 2x / 4x, Skip phase, Skip to end, Prefill rebuild feedback, Reset to start (with confirm), Toggle theme.
- Individual shortcuts for the most used actions, listed in the panel and in the operator guide.

*As built (M4):* Shift+O shows and hides the panel; it is hidden on every page load. It sits bottom right over every screen, in the existing tokens, headed "Demo", with four groups: Knowledge (Load sample Seed, Clear Knowledge, Start Build), Build (Speed 1x, 2x, 4x; Skip phase; Skip to end), Rebuild (Prefill feedback) and Lab (Reset to start, Toggle theme). Every action is a button showing its shortcut (`seed-reuse-notes.md` §6.2), and the shortcuts work with the panel hidden. Opening it moves focus into it; Escape or Shift+O closes it and puts focus back. A status line under the groups says what the last action did, or why it could not run. Load sample Seed loads at once on an empty intake and asks first otherwise ("replaces all N knowledge files, Misc Context included", OQ-17); Clear Knowledge and Reset to start always ask; Load sample and Reset open the Knowledge page. The screen says "Clear Knowledge", not "Clear intake" (requirements §5). Until M5 the Build group says builds have not arrived: speed is remembered and shown, skip does nothing; Prefill waits for the rebuild modal (M10). Shortcuts are ignored in text fields, in a modal that is not theirs, and Shift+Enter on a focused button (D-47). Server side: D-46.

*As built (M5, D-48, D-53):* Start Build (Shift+Enter) starts the build and opens its page; the status line reads "Build started: iteration 1.". Speed is kept by the server, which paces builds with it: the panel loads it when it mounts, shows a press at once and says "Speed 2x."; it can be set at any time and survives Reset. Skip phase and Skip to end are available only while a build runs ("No build is running, so there is nothing to skip."), and say "Skipping to the end of Assay." or "Skipping to the end of the build.". The Build group's note reads "Speed paces builds and is kept across Reset. Skip works while a build runs."
