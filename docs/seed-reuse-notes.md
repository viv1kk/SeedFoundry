# SeedFoundry: Seed v0.1 reuse notes

Written in M0 (2026-10-03) from a full read of `docs/seed_docs/`. For each item in `requirements.md` §9 ("What we take from Seed v0.1") this records where it lives in the Seed docs, exactly what SeedFoundry reuses, and where the Seed docs contradict ours. §5 is the binding description of the dashboard (FR-D-1).

**Read this before reusing anything.** Seed v0.1's own precedence applies to its docs: code, then `requirements.md`, then `project-notes.md`; `decisions.md` over `implementation-plan.md`. The as-built references (`architecture.md`, `design-system.md`, `operator-guide.md`) are the most reliable. `project-notes.md` §§1 to 82 are aspiration and are not what was built.

**Two vocabularies.** Seed v0.1's code says `solution`, `INIT`, `RUNTIME`, `CLOSING_SEEDING`, `feasibility`; its screen says Agent Component, Planting, Life, Cleanup, Potential (Seed `decisions.md` D-11, `architecture.md` §2). These notes give the code term first where it matters.

**What the Seed docs do not contain.** No source code, no `tokens.css`, no seed files (`core.md`, `adaptation.md`, `protection.md`), no generator, no screenshots. Every value below is quoted from prose and tables. Where a value is missing, it says so (risk R-4).

Citations use the form `seed:file §section`, all under `docs/seed_docs/`.

---

## 1. Design system

**Where:** `seed:design-system.md` §§1 to 9 (as built, source of truth was `frontend/src/design/tokens.css`); `seed:decisions.md` D-5 and OQ-3; `seed:project-notes.md` §84.5 "M21 · Design pass" (contrast fixes, fonts).

### 1.1 Principles we keep

1. Colour carries meaning, never decoration. Every colour is a token with a stated role; a value that means something has one colour on every chart, chip and table.
2. Fault colour is for faults. Red only for a technical error, a refusal, or a finding drawn as an anomaly. A request for a person's input is never red or amber.
3. Weight, not movement, shows state. Animation marks a real change and stops when it has landed.
4. Dense, not cluttered. Small type, monospace for figures and identifiers, thin borders instead of heavy cards.
5. Nothing generic-AI: no decorative gradients, no glow, no robot illustration, no futuristic styling.

### 1.2 Themes

- Light values on `:root`; dark overrides the same names under `[data-theme='dark']` set on `<html>`. No component knows the theme.
- First visit follows `prefers-color-scheme`. A toggle (Shift+D) is remembered in `localStorage`. Seed's key was `systems-v1.theme`; SeedFoundry uses `seedfoundry.theme`.
- Charts re-resolve their colours on theme change (D-5).

### 1.3 Colour tokens (copy these values)

Surfaces, lines and text:

| Token | Light | Dark | Use |
|---|---|---|---|
| `--surface-base` | `#f7f8fa` | `#0e1116` | Page and pane background |
| `--surface-raised` | `#ffffff` | `#161b22` | Cards, top bar, panels |
| `--surface-sunken` | `#eef0f4` | `#090c10` | Inputs, wells |
| `--surface-overlay` | `#ffffff` | `#1c222b` | Drawers, overlays, modals |
| `--border-subtle` | `#e2e5eb` | `#21272f` | Dividers |
| `--border-default` | `#cbd0d9` | `#2f3742` | Card and control borders |
| `--border-strong` | `#9aa2b1` | `#4a5461` | Emphasised outlines |
| `--text-primary` | `#12151b` | `#e8ebf0` | Body text and figures |
| `--text-secondary` | `#4a5261` | `#a8b1bd` | Supporting text |
| `--text-muted` | `#666e7a` | `#808995` | Labels, hints, timestamps |
| `--text-inverse` | `#f7f8fa` | `#0e1116` | Text on filled controls |

Accent and status:

| Token | Light | Dark | Means |
|---|---|---|---|
| `--accent` | `#1e61f5` | `#5b8cff` | Cobalt. Primary actions, current phase, work in progress |
| `--accent-subtle` | `#ebf1fe` | `#15203a` | Selected rows, a node awaiting input |
| `--status-positive` | `#1b7d4a` | `#3fb27a` | Done, validated, allowed, approved |
| `--status-warning` | `#9a6100` | `#d79a3a` | Caution, escalation, partial |
| `--status-negative` | `#c0392f` | `#e5705f` | A fault, a DENY |
| `--status-neutral` | `#5a6172` | `#808995` | A state of knowledge: insufficient, unverified |

Chart roles (descriptors name a role, never a hex value; the renderer reads `--chart-<role>` at paint time):

| Role | Light | Dark | Bound to in Seed v0.1 |
|---|---|---|---|
| `series-1` | `#1e61f5` | `#5b8cff` | Assigned seats (licence line) |
| `series-2` | `#6b4fd8` | `#9a82f0` | |
| `series-3` | `#0c7f7f` | `#35b8b8` | |
| `series-4` | `#a16500` | `#d79a3a` | |
| `series-5` | `#b8437c` | `#e06fa8` | |
| `series-6` | `#5d7c19` | `#9cc95a` | |
| `series-7` | `#8a5a2b` | `#c49a6c` | |
| `series-8` | `#3d6f8f` | `#7fb0d0` | |
| `positive` | `#1b7f4b` | `#3fb27a` | Active seats |
| `warning` | `#9c671a` | `#e0a84a` | Underused seats |
| `negative` | `#c0392f` | `#e5705f` | Leaver seats |
| `anomaly` | `#cc431e` | `#ff7a4d` | Unused seats; the primary KPI's top rule |
| `baseline` | `#8c95a6` | `#5b6777` | Normal or total series |
| `muted` | `#cbd0d9` | `#2f3742` | Unassigned seats |

Not needed by SeedFoundry: the Potential grade tokens (`--grade-*`) and the growth-tree tokens (`--growth-*`). We do not take the growth tree (requirements §9).

### 1.4 Type, space, shape, motion

- **Faces:** Inter (`--font-sans`) for prose, headings, labels; JetBrains Mono (`--font-mono`) for figures, identifiers, ids, timestamps, log lines. Both variable fonts bundled from npm (`@fontsource-variable/inter`, `@fontsource-variable/jetbrains-mono`), never fetched. Fallbacks Segoe UI and Consolas. Charts painted before the faces load must be redrawn once they arrive (ECharts draws text to canvas once).
- **Sizes:** `--text-xs` 11 px (small-caps labels, chips), `--text-sm` 13 px (tables, supporting), `--text-md` 15 px (body default), `--text-lg` 18 px (panel headings), `--text-xl` 24 px (KPI figures), `--text-2xl` 32 px (screen titles). Capitals labels at 0.06 to 0.08 em letter-spacing. Body line height 1.5.
- **Space:** 4 px steps, `--space-1` (4 px) to `--space-12` (48 px).
- **Radius:** 3 px chips, buttons, small controls; 6 px cards, KPI tiles, chart cards; 10 px reserved (Seed used it only for the seed screen's layer cards).
- **Depth:** `--shadow-sm`, `--shadow-md`, used sparingly; borders separate surfaces more often than shadows.
- **Motion:** `--duration-fast` 120 ms, `--duration-base` 220 ms, `--duration-slow` 400 ms, eased by `--ease-out`. Every animation tied to a state change. Under `prefers-reduced-motion` every animation and transition is cut to 0.01 ms.
- **Scrollbars:** thin, `--scrollbar-thumb` on a clear track.

### 1.5 Contrast test (port in M2)

Seed's `backend/tests/test_design.py` read `tokens.css` and checked, in both themes, against WCAG 2.1:

- every text token on every surface, and on the selected-row tint, at 4.5:1;
- the primary button label on the accent, at 4.5:1;
- every chart role against the panel surface, at 3:1, except `muted`;
- every chart label on its fill at 4.5:1 (light text on filled roles, dark text on `baseline` and `muted`).

SeedFoundry ports the same rules (NFR-6) and adds the console surface pairs (see 1.6). Any new or changed token must pass.

### 1.6 Gaps and contradictions

- **Missing values.** The docs give no values for `--shadow-sm`, `--shadow-md`, `--ease-out`, `--chart-grid`, `--chart-brush`, `--scrollbar-thumb`, `--scrollbar-thumb-hover`, the font stacks beyond the face names, or the intermediate space steps. M2 picks values consistent with the tokens above and records them (R-4).
- **No `info` token.** `build-simulation.md` §4 and `ui-spec.md` §3 colour API console lines "info". Seed v0.1 has no info token. Proposal for M2/M6: add `--console-api` (a teal from the `series-3` hue) and test its contrast on the console surface.
- *As built (M2):* the missing values, the chart label tokens and the console tokens (including `--console-api`) are chosen in D-37 and live in `frontend/src/styles/tokens.css`. The contrast test (`frontend/tests/contrast.spec.ts`, vitest) ports §1.5's rules, adds the console pairs and the accent and status colours used as text, and reads the Seed values from the §1.3 tables to check `tokens.css` still holds them.
- **Console as a terminal.** `ui-spec.md` §3 asks for a monospace console on a dark surface in both themes. Seed's activity stream was deliberately "an auditable activity stream, not a developer terminal" (`seed:requirements.md` FR-E8). Not a conflict for SeedFoundry (our build page is a lab console by design), but the light theme then needs a dark console surface. Proposal: console tokens that reuse the dark theme's `--surface-sunken`, `--text-*` and status values in both themes, covered by the contrast test.

---

## 2. Architecture patterns

**Where:** `seed:architecture.md` §§1, 4, 5, 6, 7, 8; `seed:implementation-plan.md` §2; `seed:decisions.md` D-1, D-5, D-8, D-9, A-2; `seed:project-notes.md` §84.5 "M22" (engine fix, determinism test).

### 2.1 State snapshot

- One in-memory state object is the sole source of truth (Seed FR-L5). Simulated workers record into it and never hold authoritative state.
- `GET /api/state` returns the full snapshot with the `sequence` it is current as of. The frontend adopts the snapshot, then applies events from that sequence on (Seed FR-E5).
- Reset is not a lifecycle edge: it rebuilds state from nothing.
- SeedFoundry difference: our state persists to JSON under `var/` (D-3). Seed v0.1 deliberately persisted nothing (`seed:requirements.md` §4.1).

### 2.2 Event log and SSE

- Every event carries a sequence contiguous from 1 within a run, a machine `type` (contract, drives reducers) and display fields (`category`, `severity`, `message`). Neither side can break the other.
- SSE frame `id` = sequence, `event` = type. The browser reconnects with `Last-Event-ID` and the server replays exactly from the retained log (Seed FR-E7). Keepalive comment every 15 s on an idle stream.
- A detected sequence gap makes the frontend discard local state and re-snapshot (Seed FR-E6).
- The log is unbounded within a run (Seed D-9). A Seed v0.1 run had about 140 events and needed no virtualisation; scrolling held 17 ms frames (Seed OQ-4).
- The frontend subscribes to each type by name, and a backend test fails if the backend emits a type the frontend list lacks (`test_frontend_contract.py`). Worth copying.
- Presentation is derived from the type by suffix (`.failed`, `.timeout`, `.error` are faults, and so on), in one table mirrored front and back.
- SeedFoundry's event shape (`build-simulation.md` §3) uses `seq` and `sim_t`; Seed used `sequence` and `timestamp`. Ours stands.

### 2.3 The replaceability seam

- Seed's API never imported the engine. It depended on an `EventSource` protocol (`status`, `speed`, `start`, `resolve_human`, `set_speed`, `skip_phase`, `reset`, `snapshot`). The engine recorded into state; the SSE route read from state through an event bus. One module (`runtime.py`) named the implementation.
- SeedFoundry keeps the same shape for its build engine and adds the two narrower seams of D-22: `LLMClient` and `SeedClient`, simulated only.

### 2.4 Beat engine with weights (timing approach)

- Workflows are Python generators yielding beats. A beat is a relative weight, never a time. The runner sleeps `weight x total_seconds / total_weight` (Seed: 270 s over 105 units), or the beat's floor in seconds if longer. Floors protect meaning-bearing beats from being compressed out of sight.
- Speed divides every remaining delay; skip drops delays until the phase changes. Both act within 50 ms because each sleep is cut into 50 ms slices.
- **M22 lesson, copy it:** read beat progress from the event loop's clock, not by adding up requested slices. Counting slices made the 270 s narrative take 297 s under load.
- **SeedFoundry difference that matters for determinism:** our `sim_t` is simulated seconds computed from the schedule (cumulative weights scaled to 75 s), never from the clock. Speed, skip and machine load then change pacing only (FR-DC-4), and `sim_t` is identical across runs.
- SeedFoundry's budget: weights sum to 100 over 75 s at 1x (D-7), so one unit is 0.75 s.

### 2.5 Descriptor-driven dashboards

- One generic renderer draws every dashboard from a backend descriptor (Seed D-1). No dashboard is a hand-written component.
- Chart specs carry mark type, data binding, semantic colour role, visual weight and layout: span, height, emphasis, questions, notes, empty states (Seed R-6 final status). Never hex (D-5).
- Mark vocabulary is deliberately small: `kpi`, `line`, `bar` (vertical or horizontal, optionally stacked), `treemap`, `table` (Seed OQ-1 "What OQ-1 and OQ-2 mean").
- Every figure is aggregated from rows at request time; the frontend holds no analytical logic (Seed FR-AN5).
- SeedFoundry fit: the defect overlay (D-13) is a set of descriptor patches plus `defects.css`. Visual QA (T-17 to T-20) runs over the descriptor and resolved token values; the off-palette defect (V-3) is the one place a hex value appears, inside the overlay only.

### 2.6 Policy evaluation

- `seed:architecture.md` §8: a request states an action, a resource and facts, and never names a rule. Every covering rule whose facts hold matches; the strictest effect wins (DENY over ESCALATE over ALLOW) and the most specific rule of that effect is cited. A request missing a fact some rule depends on is denied under the default rule (PR-000).
- Reuse for SeedFoundry's Stress & Probe protection probes (T-13): probes are requests against rules derived from the intake's Protection layer, evaluated the same way, so a probe result is computed, not printed.
- Do not take Seed's rule ids (PR-xxx) as SeedFoundry ids (requirements §9). Seed's ids may appear only inside simulated Seed v0.1 log lines, labelled as the Seed's.

### 2.7 Determinism testing

- Seed's NFR-D4 as amended by A-2: equal modulo timestamps and durations, compared leaf by leaf. The M22 test found that dropping keys that "look like times" would have hidden a difference (`decidedAt` held a sequence number). SeedFoundry's version: exclude exactly `wall_ts` and nothing else.
- Two cheap guards from `test_rehearsal.py` worth copying early: no URL in the code names a host other than this machine (NFR-2), and no model library is a dependency (D-1).

---

## 3. Lifecycle: Planting, Life and Cleanup

**Where:** `seed:architecture.md` §§3, 4; `seed:requirements.md` FR-L9, FR-C1 to FR-C7, FR-LF4 to FR-LF11; `seed:decisions.md` D-16, D-17, D-20; `seed:project-notes.md` §84.5 "M18", "M19", "M22".

### 3.1 Seed v0.1's lifecycle as built

Twelve states, one transition table; an illegal move raises (409 over HTTP). Waiting on a person is a `blockedOn` flag, not a state.

| Phase (code) | Screen name | States | What happens |
|---|---|---|---|
| `INIT` | Planting | `UNINITIALIZED` → `INITIALIZED` | The three layers are validated, heading-parsed and planted. `seed.loaded` carries a per-layer summary (title, heading count, section count, topics) and the declared stack: the five systems the Adaptation layer names, each "Declared, not yet verified" |
| `DISCOVERY` | Discovery | `DISCOVERING`, `DISCOVERY_BLOCKED`, `DISCOVERY_COMPLETE` | Five systems expand to about 30 nodes; one credential pause; one endpoint timeout, retried and recovered; summary "5 systems, 6 data sources, 17 datasets (16 profiled, 1 excluded by policy)" |
| `ASSESSMENT` | Assessment | `ASSESSING`, `AWAITING_APPROVAL` | Each methodology graded HIGH, MEDIUM, PARTIAL or LOW from field completeness. License Optimization is PARTIAL (unit price 64% complete). Deployment is escalated (PR-053), which raises the approval |
| `IMPLEMENTATION` | Implementation | `IMPLEMENTING`, `IMPLEMENTATION_COMPLETE` | Each approved component builds through Pending, Building, Testing, Validated, Complete, with named tests |
| `IMPLEMENTATION` | Cleanup | `CLOSING_SEEDING` | After a person confirms: consolidate working notes, purge scratch space, promote each interface to its release version, retire the build tools; then "seed consumed". Four policy-gated steps (PR-090, 091, 093, 095) |
| `RUNTIME` | Life | `READY_TO_RUN` ⇄ `RUNNING` | Agent One VW collects the final twelve simulated weeks (ISO weeks 24 to 35 of 2026), one week a step, recalibrates every four steps (three times), and ends "caught up". No person is asked anything |

Order: **Planting → Discovery → Assessment → Implementation → Cleanup → Life.** Cleanup comes before Life and belongs to the Implementation phase.

Weights in Seed: discovery 54, assessment 25, implementation 20, closing 6 (105 units over 270 s); Life's beats weigh nothing and run on floors (3 s a step, 2 s more per recalibration, about 45 s). Measured at 1x: Planting to Discovery complete 139 s, Assessment 64 s, Implementation 51 s, Cleanup 15 s.

### 3.2 What SeedFoundry reuses

- The names Planting, Life and Cleanup on screen, and `INIT`, `RUNTIME`, `CLOSING_SEEDING` as the simulated Seed API's state values.
- The order above, inside the simulated sandbox run.
- Planting's real content: three layers in (our generated `core.md`, `adaptation.md`, `protection.md`), heading summary out, declared stack listed as unverified.
- Cleanup's four operations and "seed consumed", as log lines from `SimulatedSeedClient`.
- Life's shape: a finite collection cursor (twelve weeks, three recalibrations), then caught up. For licences Seed recalibrates nothing: seats are known from the start, each month's use arrives at month end, and the utilisation class reads the last 90 days (`seed:decisions.md` D-17 "As built").

### 3.3 Contradiction with `build-simulation.md` §2 (OQ-11, resolved by D-26)

Our phase catalogue says:

- phase 8 **Life**: "Seed v0.1 RUNTIME workflows (discovery, assessment, approval, implementation) ... each human gate auto-resolved";
- phase 11 **Cleanup & Report**: "Seed v0.1 CLOSING_SEEDING", after Life, Stress & Probe and Harvest.

In Seed v0.1 discovery, assessment, approval and implementation are not RUNTIME workflows; they are the Seeding phases before Cleanup. RUNTIME (Life) is post-cleanup collection and raises no human gate. Cleanup (`CLOSING_SEEDING`) precedes Life. So as written our catalogue renames Seed's Seeding stages "Life" and runs Seed's Cleanup after Seed's Life, which contradicts requirements §9 ("Lifecycle names and order for the Planting, Life and Cleanup phases"). FR-B-5 ("every human gate that Seed v0.1 would raise during Life") has the same problem: Seed raises none during Life.

**Resolved (D-26, 2026-10-03).** Eleven phases kept, with count, order, weights and test ids unchanged. Phase 7 Planting is Seed INIT; phase 8 is **Seeding & Life** (`seeding`) with sub-steps Discovery, Assessment, Implementation, Cleanup, Life in Seed's order and all three gates inside it; phase 11 is **Teardown & Report**, SeedFoundry's own sandbox teardown. FR-B-5 is amended by A-1. `build-simulation.md` §2 is updated.

---

## 4. Human gates

**Where:** `seed:architecture.md` §4 "Requests to a person"; `seed:requirements.md` FR-H1 to FR-H7, FR-C1, FR-C2; `seed:decisions.md` §8.1 row 9, OQ-6; `seed:operator-guide.md` §4.

### 4.1 Gate list

| Request id | Kind | Raised in | Times in a Seed v0.1 run | Answer body | Notes |
|---|---|---|---|---|---|
| `servicenow-incident-api` | `credentials` | Discovery | 1 | `{ username, password }` | Nothing validated. Values used for the handshake and discarded; only field names recorded (Seed FR-H5) |
| `solution-approval` | `approval` | Assessment | 3 (asked again while any component awaits a decision) | per component: `{ decision: approve or reject }` | Raised as the consequence of ESCALATE on deployment (PR-053) |
| `close-seeding` | `confirmation` | Implementation, before Cleanup | 1 | `{ acknowledged: true, choice: "close" }` | Its one option reads "Run, clean up and close seeding" on screen (Seed FR-C1; the original label uses a dash we do not reproduce) |

Defined and styled but never raised by the scripted run: `ambiguity`, `missing-info`. Each request states what is needed, what access, and why (Seed FR-H2).

Related policy decisions in the same run: one DENY (PR-033, reading ServiceNow's security log as a usage signal, an expected refusal the run carries on from) and one ESCALATE (PR-053, deployment). They are not gates, but a faithful simulated log shows them.

### 4.2 How SeedFoundry auto-resolves them (proposal, for M5)

All three are resolved inside phase 8, Seeding & Life, in Seed's order (D-26). SeedFoundry's Seed carries one methodology (License Optimization), so `solution-approval` is raised once, not three times. The gate ids and kinds are kept exactly.

| Gate | Resolved from | Log wording sketch |
|---|---|---|
| `servicenow-incident-api` (credentials) | `environment.md` Protection layer (access and credential rules) and Data layer (sources) | "Gate servicenow-incident-api (credentials) auto-resolved: sandbox read-only credential issued (simulated), values not stored. Basis: environment.md, Protection" |
| `solution-approval` (approval) | `music.md` Decision Logic and Value Logic; the Seed's Potential (PARTIAL is approvable, Seed FR-A5) | "Gate solution-approval (approval) auto-resolved: approve License Optimization at potential PARTIAL. Basis: music.md, Decision Logic" |
| `close-seeding` (confirmation) | `environment.md` Protection layer (guardrails) and `music.md` Decision Logic | "Gate close-seeding (confirmation) auto-resolved: close seeding. Basis: environment.md, Protection" |

The cited section is computed: the resolver looks for the named section heading in the intake file, and cites the first matching heading it finds. If the section is missing the gate still resolves, and the log says it resolved on default.

**Contradiction:** `build-simulation.md` §4's example line "Gate H-02 auto-resolved" uses an id Seed v0.1 never had. Requirements §9 takes Seed's gate ids, so logs use `servicenow-incident-api`, `solution-approval`, `close-seeding`.

*As built (M5):* as proposed, with `solution-approval` raised once. Each gate is one `gate.auto_resolved` event (`code` the gate id; `data` the kind, stage, resolution and `basis` with file, section and line, or null). The basis lists are: `servicenow-incident-api` environment.md Protection, then Data; `solution-approval` music.md Decision Logic, then Value Logic; `close-seeding` environment.md Protection, then music.md Decision Logic. A heading matches when it contains those words, so the sample cites "Protection Layer" and "Decision Logic". Without any, the line ends "No matching section in Knowledge, so it resolved on default". Seed's request is logged first ("Seed v0.1 raised request ... (simulated)"), and the answer after as an `api.call`.

**Oddity to be aware of:** the credential gate is for ServiceNow's Incident API, which License Optimization does not use (it reads the License Management System and SAP). Seed v0.1's discovery raised it regardless of methodology, so a faithful simulation keeps it.

---

## 5. Dashboard

**Where:** `seed:decisions.md` §4 "What OQ-1 and OQ-2 mean" (the ruling and its "As built" list); `seed:project-notes.md` §84.5 "M20 · Remaining dashboards" (live figures) and "M21" (treemap crumb); `seed:architecture.md` §6; `seed:design-system.md` §3 chart roles and §6 layout; `seed:operator-guide.md` §6 (unit price completeness).

This section is the spec for the polished iteration 2 dashboard (FR-D-1, FR-D-3) and the baseline iteration 1's defects are planted against (FR-D-2). The methodology and layout are binding; the data is SeedFoundry's own (D-30, 5.7).

### 5.1 Identity

| Item | Value |
|---|---|
| Methodology | License Optimization |
| Seed v0.1 solution id | `license-optimization` |
| Dashboard title on screen | **License Optimization** (D-27). Seed v0.1's as-built title was "Licence Utilisation"; SeedFoundry does not use it |
| Systems it draws on | License Management System (entitlements, assignments, usage) and SAP (contract items, unit price) |
| Period | Twelve months of monthly usage (Seed v0.1: September 2025 to August 2026) |
| Records | Seed v0.1: 13,620 entitled seats, and 163,440 seat-months of activity (13,620 x 12). SeedFoundry: its own count (D-30) |
| Products and vendors | Seed v0.1: 20 products from 10 vendors. SeedFoundry: its own (D-30) |
| Potential | PARTIAL: `sap.contract_item.unit_price` is 64% complete. Raising it to 95% would grade HIGH (`seed:operator-guide.md` §6) |
| Cost rule | Cost is stated for priced products only; where there is no price it is withheld, never estimated (Seed PR-074). Unpriced products show as withheld, not zero |

### 5.2 The record

A seat. Utilisation class has five values. Colours from the chart roles:

| Class | Meaning | Chart role | Recoverable |
|---|---|---|---|
| Active | Assigned and in use | `positive` | No |
| Underused | Assigned, used below threshold | `warning` | No |
| Unused | Assigned, not used | `anomaly` | Yes |
| Leaver | Assigned to someone who has left (an access finding) | `negative` | Yes |
| Unassigned | Entitled seat with no assignee | `muted` | Yes |

The class reads the snapshot's last 90 days. Seed's line chart binds assigned seats to `series-1`.

Record fields (record table "Seats"): seat id (format `LIC-001848`), product, department, assignee, last used, days idle, utilisation class, unit cost. Vendor is a property of the product.

### 5.3 Layout

Seed's common four bands (`seed:design-system.md` §6), in this order:

1. KPI row.
2. Chart grid, twelve columns, the first chart spanning the full width.
3. A focused table on a subset of columns.
4. The full record table, paginated and sortable.

Above the bands in Seed: a drill bar with Back, breadcrumb, collection state and an Evidence button. SeedFoundry keeps the drill bar with Back and the breadcrumb (D-29, FR-D-6). It drops the collection state, because the dashboard shows the caught-up dataset, and the Evidence button, unless OQ-15 says otherwise.

### 5.4 Panels

Panel ids are SeedFoundry's (Seed's descriptor ids for this dashboard are not recorded). Titles marked "as built" are Seed's; the others are SeedFoundry wording for a panel Seed describes but does not title.

| Panel id | Band | Title | Mark | Data | Colour |
|---|---|---|---|---|---|
| `k-entitled` | KPI | Entitled | kpi | count of seats | primary KPI: `anomaly` top rule (Seed's convention) |
| `k-assigned` | KPI | Assigned | kpi | seats with an assignee (all classes but Unassigned) | text |
| `k-active` | KPI | Active | kpi | seats in class Active | text |
| `k-idle` | KPI | Unused or underused | kpi | seats in Unused or Underused | text |
| `k-recoverable` | KPI | Recoverable a year | kpi, currency | sum over recoverable seats on priced products of unit cost x 12; note "priced products only, N seats withheld" | text |
| `seats-treemap` | Chart, full width | Seats by vendor and product | treemap | vendor, then product, then class; sized by entitled seats | by class |
| `entitlement` | Chart | Entitled, assigned and active by product | bar, horizontal, grouped | per product: entitled, assigned, active. "The gap is the finding" | `baseline` (entitled), `series-1` (assigned), `positive` (active) |
| `trend` | Chart | Assigned and in use, by month (as built) | line | per month, estate-wide: assigned seats and seats in use | `series-1` (assigned), `positive` (in use) |
| `recoverable` | Chart | Recoverable cost by product | bar | per product: recoverable cost a year; unpriced products shown as withheld, not zero | `anomaly` |
| `candidates` | Focused table | Optimisation candidates (Seed: "optimisation candidates per product") | table | per product: vendor, entitled, active, underused, unused, leaver, unassigned, recoverable a year; total row | class chips |
| `seats` | Record table | Seats (as built) | table | one row per seat, fields in 5.2; footer with class counts and total | class chip |

Seed's ruling and its as-built notes give four charts and both tables, "within FR-AN7's roughly 3 to 4". The treemap's legend lists the five classes with each class's share of entitled seats; the shares sum to 100%.

### 5.5 Seed v0.1's headline figures (reference only, D-30)

SeedFoundry's dashboard shows its own data's figures (5.7). These are Seed v0.1's, recorded live in `seed:project-notes.md` §84.5 "M20" with the full dataset (Life caught up), kept as a reference for scale and proportion:

| Figure | Value | Source |
|---|---|---|
| Entitled | **13,620** | M20; `seed:architecture.md` §6; `seed:decisions.md` §4 As built |
| Assigned | **13,002** | M20 |
| Active | **9,496** | M20 |
| Unused or underused | **3,171** | M20 |
| Recoverable a year | **$390k**, priced products only, **975 seats withheld** | M20 |
| Drill example | Microsoft 365 E3, Unused: **104 seats, $45k** | M20 |
| Products, vendors | **20, 10** | `seed:decisions.md` §4 As built |

Derived from the above (arithmetic, to be confirmed when the generator is written):

| Figure | Value | How |
|---|---|---|
| Unassigned | 618 | 13,620 minus 13,002 |
| Leaver | 335 | 13,002 minus 9,496 minus 3,171, assuming leaver seats still have an assignee |
| Unused + Leaver + Unassigned (recoverable seats) | 4,124 minus the Underused count | (3,171 minus Underused) + 335 + 618; the Unused and Underused split is not recorded |
| Implied Microsoft 365 E3 price | about $36 a seat-month | $45k over 104 seats over 12 months |
| Class shares of entitled | Active 69.7%, Unused or underused 23.3%, Leaver 2.5%, Unassigned 4.5% | from the counts above |

Two readings were ambiguous in Seed's record and no longer need settling, because the data is SeedFoundry's own: whether "975 seats withheld" counts recoverable seats on unpriced products (our reading) or every seat on an unpriced product; and the Underused versus Unused split inside 3,171.

### 5.6 Hierarchy and drill (as built, and in scope for SeedFoundry: D-29, FR-D-6)

All products → vendor → product → utilisation → seat. A treemap leaf click drills vendor, product and class in one step, and its breadcrumb crumb names all three levels ("Microsoft › Microsoft 365 E3 › Unused", per the M21 fix).

### 5.7 SeedFoundry's data (D-30)

The underlying data does not need to match Seed v0.1 (stakeholder, 2026-10-03). The **methodology** and the **dashboard layout** must. SeedFoundry writes its own seeded generator in M7, and every figure on the dashboard is that data's true count. The figures in 5.5 are reference, not targets.

**Must match Seed v0.1 (the methodology):**

- The record is a seat, with the fields in 5.2. Concepts: entitlement, assignment, usage, cost.
- Five utilisation classes with the meanings, colours and order in 5.2, read from the last 90 days of usage.
- Recoverable seats are Unused, Leaver and Unassigned. Underused is reported, not recovered.
- Recoverable cost is unit cost x 12 for priced products only. Unpriced products are withheld, never estimated, and the number of withheld seats is stated beside the KPI.
- Twelve months of monthly usage behind the trend line.
- Incomplete unit prices, which is why the methodology grades PARTIAL.

**Must match Seed v0.1 (the layout):** the four bands, the eleven panels and their marks in 5.4, the colour binding in 5.2, the hierarchy and drill behaviour in 5.6.

**Free for SeedFoundry to choose:** vendor and product names, number of vendors and products, seat count, departments, unit prices, class splits, the monthly series. Seed's scale (about 13,600 seats, 20 products, 10 vendors) is a sensible density for the panels, not a requirement. Names follow Seed's style: realistic software products.

**Not stated by Seed, so SeedFoundry defines it** (in the sample `music.md` in M4 and the generator in M7): the Underused threshold (days of use in 90), and how a leaver is identified. *Defined in M4:* in the sample `music.md`, classes are tested in the order Unassigned, Leaver, Unused, Underused, Active; Unused is no days active in the last 90, Underused 1 to 11, Active 12 or more; a Leaver is a seat assigned to someone who has left, whatever its usage. The sample `environment.md` reads "the last 90 days" as the three most recent monthly usage records and gives the seat an `assignee_status` (`employed` or `left`) from the LMS. M7's generator follows these.

**Constraints the data must meet so the tests work:**

- Every class is present in the estate, and in most products.
- At least nine priced products, so V-1's pie has more than eight slices, and at least one unpriced product, so withholding shows.
- At least two vendors with more than one product each, so every treemap level has children.
- The alternate dataset for the data-swap test (T-08) has the same schema and methodology with a different estate: other vendors, products and sizes.

### 5.8 Defect mapping (iteration 1)

`build-simulation.md` §5's panel names are placeholders. Each defect maps to the closest real panel above. Every shown value is derived from SeedFoundry's data by a fixed rule, so the validators find it by recomputing from source rows, never from a list (D-14). Rows marked **mapping choice** have no exact Seed panel; the mapping was confirmed by the stakeholder (OQ-13, D-28). The D-14 finding count is asserted on the unfiltered dashboard; the overlay rules also apply at every drill level (R-9).

| Id | Placeholder | Panel | Patch (descriptor or `defects.css`) | Derived from data by | Detected by |
|---|---|---|---|---|---|
| N-1 | Licenses by department (bar) | `entitlement` (**mapping choice**: Seed has no department chart; the per-product bar is the part-to-whole chart closest to it) | Entitled bars shown at 1.2 x true per product | bars sum to 1.2 x the Entitled KPI (with Seed's 13,620 that would be 16,344) | T-16 part sums equal KPI |
| N-2 | Utilisation distribution | `seats-treemap` legend shares (**mapping choice**) | each class share shown at 1.12 x true | shares sum to 112% | T-16 percentage set sums to 100 (±0.1) |
| N-3 | Savings KPI | `k-recoverable` against `recoverable` | KPI computed over Unused and Underused seats instead of the recoverable classes (Unused, Leaver, Unassigned) | KPI differs from the sum of the per-product recoverable bars | T-16 derived KPI equals its formula and the cost panel |
| N-4 | License status table | `seats` footer (**mapping choice**: Seed has no status table) | footer "Total" shows the assigned count (13,002) | Active + Underused + Unused + Leaver + Unassigned = 13,620, footer says 13,002 | T-16 table total equals row sums |
| N-5 | Vendor table | `candidates` total row (**mapping choice**: Seed has no vendor table; the candidates table carries vendor) | total row adds the largest product's row twice | total exceeds the sum of rows by that row | T-16 table total equals row sums |
| V-1 | Pie > 8 slices | `recoverable` | rendered as a pie with one slice per priced product | slice count = number of priced products (more than 8) | T-17 pie at most 6 slices; categorical comparison as bars |
| V-2 | Red for a normal series | `trend` | "in use" series bound to `negative` | role check | T-19 red reserved for faults |
| V-3 | Off-palette; same category two colours | `seats-treemap` and `entitlement` | Unused drawn in an off-palette hex in the treemap; Active drawn in `series-3` in the bar while `positive` in the treemap | palette membership and per-category consistency | T-19 |
| V-4 | Mixed formats, missing currency | KPI row and `candidates` | Entitled "13620", Assigned "13,002", Active "9.5k"; recoverable figures without "$" | format per measure | T-18 |
| V-5 | Missing axis labels and units, two charts or more | `entitlement` and `trend` | axis names and units removed | axis label presence | T-18 |
| V-6 | Misaligned cards, uneven gutters, overflow, truncation | KPI row, `seats-treemap`, `seats` | uneven KPI gutters and one card off the grid; treemap wider than its card; last two `seats` columns clipped | card geometry against the grid | T-19 |
| V-7 | Mixed fonts | `trend` title | panel title in a system serif | single family per role | T-19 |
| V-8 | Muted text below AA | `candidates` caption and notes | muted text set to a light grey below 4.5:1 on the card | computed contrast per text and background pair | T-20 |
| L-1 | Panel waits 4.5 s | `seats-treemap` (the build log then names "Seats by vendor and product", not "Spend by vendor") | declared latency 4.5 s, spinner shown | declared value against the 1.0 s budget | T-15 |

Total 14, as `build-simulation.md` §5 requires. The figures in the N-1 log line are whatever SeedFoundry's data gives; at Seed's scale it would read "KPI shows 13,620, product chart sums to 16,344".

---

## 6. Operator pattern

**Where:** `seed:operator-guide.md` §§3 to 7; `seed:requirements.md` FR-O1 to FR-O4, FR-S7; `seed:project-notes.md` §84.5 "M22" (the capital-letter defect).

### 6.1 Seed v0.1's controls

| Keys | Does |
|---|---|
| Shift+O | Show or hide the operator panel |
| Shift+P | Load the bundled seed files |
| Shift+Enter | Plant the seed; once planted, start the run |
| Shift+1 / Shift+2 / Shift+0 | Speed 1x / 2x / instant |
| Shift+S | Skip to the end of the current phase |
| Shift+R | Reset |
| Shift+D | Toggle light and dark |

Rules: all on Shift; none fires while focus is in a text field (M22 fixed a defect where typing "Rachel" reset the run at the capital R); no visible transport bar; the panel shows state, run status, stream connection, event count and gaps, has a button for every shortcut, and adds rehearsal tools (open any dashboard without a run, revise evidence). Speed and skip change timing only and act within 50 ms. Speed survives Reset.

Seed read the typed character, so Shift+1 assumed a US layout (it types `!`).

### 6.2 SeedFoundry's map (closes OQ-5)

| Keys | Does | Note |
|---|---|---|
| Shift+O | Show or hide the demo controller | as Seed |
| Shift+P | Load sample Seed | as Seed's "load bundled seed" |
| Shift+Enter | Start Build (when enabled) | as Seed's start |
| Shift+1 / Shift+2 / Shift+4 | Speed 1x / 2x / 4x | 4x replaces Seed's instant (FR-DC-2) |
| Shift+S | Skip to end of phase | as Seed |
| Shift+E | Skip to end of build | new |
| Shift+F | Prefill rebuild feedback | new; only when the rebuild modal is open |
| Shift+C | Clear intake (asks to confirm) | new |
| Shift+R | Reset to start (asks to confirm) | as Seed |
| Shift+D | Toggle light and dark | as Seed |

Shortcuts are ignored while focus is in an `input`, `textarea`, `select`, a `contenteditable` element, or the editor. Digits are matched on `KeyboardEvent.code` (`Digit1`, `Digit2`, `Digit4`), so they work on any layout; letters on `key`, case-insensitive. No browser default collides: Chrome uses Ctrl or Alt chords, not Shift plus a letter.

*As built (M4, D-47):* the map is `frontend/src/demo/shortcuts.ts`. Also ignored: any shortcut with Ctrl, Alt or Meta, key repeats, anything under `[data-no-shortcuts]`, every shortcut while a modal is open unless it belongs to that modal (Shift+F belongs to the rebuild modal), and Shift+Enter on a focused button or link, where Enter is already that control's. The Knowledge editor is a `textarea`, so the editor rule is the textarea rule. Speed is kept in the browser until M5 and survives Reset, as Seed's did. *M5 (D-48):* speed is kept by the server's build engine, still survives Reset, and acts within 50 ms, as do both skips; none of them emits an event.

### 6.3 Demo script and rehearsal

Copy the operator guide's structure for `docs/operator-guide.md` in M12: set up once per machine, start and stop, controls, a timed demo table (when, on screen, what you do), rehearsing, checks before a demo, troubleshooting (stale server on a port, Application Control blocking uv, use the printed address).

---

## 7. Process

**Where:** `seed:README.md` (precedence); `seed:decisions.md` (format of rulings, amendments, §8 as-built reconciliation); `seed:implementation-plan.md` §3 (status table with commits, RENAME, MOVE, NEW tags); `seed:project-notes.md` §84.5 (build log).

Already adopted in `methodology.md`: requirements, decision record with D-n, OQ-n, R-n; amendments A-n with strike-through; milestone plan with exit criteria; one build log entry per milestone; as-built reconciliation at the end.

Further practices worth keeping:

- Every build log entry ends with **"Check by hand"**: the steps the stakeholder should do in the browser.
- A **status table with the commit** for each milestone.
- Live checks on an **isolated copy of the app on other ports**, because a browser left open on the shared app changed its state mid-check (Seed D-19 follow-up).
- **Restart stale servers** after backend changes: a pre-change server on the port made a working feature look broken (Seed M18 follow-up).
- **Timing tests flake under load.** Seed ruled its marginal 200 ms test noise. Our timing tests should measure the simulated clock, not wall time, wherever possible.
- **Audit before renaming** anything load-bearing (Seed M12), and list "silent failure" references (CSS selectors on values, ids matched across the boundary) that no test catches.

---

## 8. Stack and delivery (OQ-1)

**Where:** `seed:requirements.md` NFR-L1 to NFR-L4; `seed:architecture.md` §1; `seed:operator-guide.md` §1; `seed:decisions.md` D-10, D-21.

| Item | Seed v0.1 | SeedFoundry (D-2) |
|---|---|---|
| Python | 3.12 or newer | 3.12.10 on the target machine |
| Node | 20 or newer | 24 on the target machine |
| Backend | FastAPI under uvicorn, every route under `/api` | same |
| Frontend | Vue 3 + TypeScript + Pinia + Vite; Vite proxies `/api` | same |
| Charts | Apache ECharts, colours from tokens at runtime (D-5) | same, bundled from npm, added in M7 |
| Transport | SSE | same |
| Frontend tests | none (typecheck and build only) | vitest (D-2) |
| Python env | uv (`uv.lock`), with `run.ps1` for machines where uv is blocked; requirements files exported from the lock | same (D-25) |
| Launcher | `run.py` (waits for both servers, prints a ready line) and `run.ps1` | same (D-23) |
| Ports | 8000 and 5173 | 8100 and 5273 (OQ-8 assumption) |
| Data | pandas | not needed at 13,620 rows; decided in M7 |

Seed's Vite bound to `localhost` only, so `127.0.0.1:5173` did not answer and the guide had to warn about it. SeedFoundry binds Vite to `127.0.0.1` and prints that address (D-23).

---

## 9. What we do not take

Confirmed against the Seed docs (requirements §9, right column):

- **ACME specifics** beyond the License Optimization data: the other two methodologies and their dashboards, the environment graph and its coordinates, the five-system narrative as screens (the simulated Seed API may still name the systems in its logs).
- **Seed v0.1 rule ids** as SeedFoundry ids (PR-xxx stays inside simulated Seed log lines).
- **The growth tree** and its tokens.
- **Seed and Life naming for SeedFoundry's own screens.** Our screens are Knowledge, Build, Review, Seed. "Seed" is both our final screen's name and the product being formed; Seed v0.1 is always written with its version.
- Also not taken: Agent One VW and ValueWise naming, Potential's colour scale, the routing-problem flag, the evidence revision tool, the Seeding and Life two-pane layout.

---

## 10. Contradictions and gaps, in one list

| # | Our doc | Seed docs say | Status |
|---|---|---|---|
| 1 | `build-simulation.md` §2 phase 8 "Life" runs discovery, assessment, approval, implementation with gates | Those are Seeding phases; Life is post-cleanup collection with no gates | Resolved: D-26 |
| 2 | `build-simulation.md` §2 phase 11 runs CLOSING_SEEDING after Life | Cleanup precedes Life | Resolved: D-26 |
| 3 | FR-B-5 "gates Seed v0.1 would raise during Life" | No gate is raised during Life | Resolved: A-1 |
| 4 | `build-simulation.md` §4 "Gate H-02" | Gate ids are `servicenow-incident-api`, `solution-approval`, `close-seeding` | Use Seed ids (§4) |
| 5 | "License Optimization dashboard" (FR-D-1, `ui-spec.md` §5) | Dashboard is titled "Licence Utilisation" | Resolved: title is License Optimization (D-27) |
| 6 | `build-simulation.md` §5 panels: by department, utilisation distribution, status table, vendor table | No such panels; nearest real panels in §5.8 | Resolved: map, add none (D-28) |
| 7 | N-3 "current spend minus optimised spend" | Seed shows recoverable cost directly, not current and optimised spend | Recast as KPI against the cost panel (§5.8) |
| 8 | Console "API (info)" colour | No info token | Resolved: `--console-api` (D-37) |
| 9 | Dashboard scope (FR-D) is silent on interaction | Seed's dashboard is fully interactive: cross-filter, drill to seat, evidence panel, collection step | Resolved: drill-down in (D-29, A-2); evidence panel open (OQ-15) |
| 10 | `requirements.md` §9 "contrast test" | Seed's test is Python over `tokens.css` | Resolved: rules ported to vitest (D-38) |
| 11 | `implementation-plan.md` M2 "port tokens.css" | `tokens.css` is not in the Seed docs; only its values in tables, some missing | Resolved: rebuilt from §1.3 in M2, gaps filled (D-37) |
| 12 | `implementation-plan.md` M7 "License Optimization data" | No data or generator in the docs; only headline figures | Resolved: data is SeedFoundry's own; methodology and layout match (D-30, §5.7). M7 authors the generator and an alternate dataset |
