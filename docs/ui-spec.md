# SeedFoundry: UI spec

The four screens, the rebuild modal and the demo controller. This describes intent and layout; exact visuals come from Seed v0.1's design system (`seed_docs/design-system.md`) and are recorded in `seed-reuse-notes.md`. Claude Code may improve layout details for cohesion as long as every requirement in `requirements.md` holds.

## 1. App shell

- Top bar: SeedFoundry wordmark (left), journey indicator (centre): **Knowledge → Build → Review → Seed**, iteration badge ("Iteration 1 of 2") when a build exists, theme toggle (right).
- The journey indicator shows where you are; earlier steps are clickable when it makes sense (e.g. back to Knowledge to read files, which are read-only during a build).
- Routes (suggested): `/knowledge`, `/build/:iteration`, `/review/:iteration` (report), ~~`/review/:iteration/dashboard`~~ `/review/:iteration?dashboard=license-optimization&drill=...` (dashboard over the report, OQ-4 closed in M0; `drill` carries the drill path, D-29), `/seed`. Follow Seed v0.1's routing and dashboard-view pattern where it applies (OQ-4).

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

## 4. Review: report

- **Header:** verdict chip (iteration 1: "Completed with findings"; iteration 2: "Passed"), iteration, total duration, counts (phases, tests, findings).
- **Findings:** grouped Numeric, Visual, Latency, Boundary. Each row: id, panel or file, expected, shown, severity, found in phase. Clicking a dashboard finding opens the dashboard with that panel highlighted.
- **Tests:** table of every test run (id, phase, name, result).
- **Auto-resolved gates:** each Seed v0.1 human gate with how it was resolved.
- **Simulated usage:** LLM calls, tokens in/out, API calls, sandbox time. Label clearly as simulated in small text.
- **Iteration 2 only:** "Changes since iteration 1" section: each previous finding marked resolved, plus the observer feedback quoted in a blockquote.
- **Actions (sticky footer):** View Dashboard (secondary), Rebuild (secondary, iteration 1 only), Approve (primary).

## 5. Review: dashboard

- Iteration 2: Seed v0.1's License Optimization dashboard as recorded in `seed-reuse-notes.md`, polished.
- Iteration 1: same dashboard with the defect overlay (see `build-simulation.md` §5). It should look clearly unfinished at a glance, not subtly off.
- A thin SeedFoundry frame around it: "Back to report", iteration badge, and (iteration 1) a small "N findings" link back to the report.
- Title on screen: **License Optimization** (D-27).
- **Drill-down (FR-D-6, D-29), both iterations:** a drill bar above the bands with Back and a breadcrumb (All products › vendor › product › class). Clicking a treemap cell or a bar drills; every panel follows the drill; the deepest level is the Seats table for that selection. The browser's Back pops one step, and reload keeps the path. A treemap leaf drills several levels in one click and its crumb names each level, as in Seed v0.1. In iteration 1 the defect overlay stays applied at every level.

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
