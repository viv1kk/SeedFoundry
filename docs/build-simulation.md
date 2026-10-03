# SeedFoundry: Build simulation spec

How a build runs: phases, sub-steps, timing, events, logs, planted defects, validators, generated files and the sample Seed. Everything here is deterministic (NFR-1).

## 1. Engine model

- A generator-based **beat engine** (Seed v0.1 pattern, see `seed_docs/implementation-plan.md` and `architecture.md`) walks phases and sub-steps. Each sub-step yields beats; each beat emits one or more events.
- Each phase has a **weight**. Weights sum to 100 and map to a 75 s budget at 1x (range 60 to 90 s allowed). Speed controls scale the clock only.
- All "work" a step reports is produced by real deterministic code where it is cheap to do so (Assay stats, boundary check, file generation, validators) and by `SimulatedLLMClient` / `SimulatedSeedClient` elsewhere.
- RNG: seeded from `sha256(intake content) + iteration`. Used only for cosmetic variety (sandbox id, simulated latencies within fixed bands, token counts jitter).
- State is held server-side; the client receives a snapshot then replays the event log, then streams new events over SSE.

## 2. Phase catalogue

| # | Phase (screen name) | Code id | Weight | Sub-steps | Tests in this phase |
|---|---|---|---|---|---|
| 1 | Assay | `assay` | 6 | (iter 2, first) Apply observer feedback: Route feedback to Ensemble files; Update person.md; Update instrument-awareness.md; Update environment.md; Update music.md (D-36, see §9); Inventory files; Measure Ensemble coverage per file; Ensemble boundary check; Fingerprint intake | T-01 core files present, T-02 coverage, T-03 boundary check |
| 2 | Distillation | `distill` | 12 | Load model profile from Instrument Awareness; Plan context budget; Distil Music (purpose, principles, value, decisions); Distil Person; Distil Environment layers; Merge Misc Context; (iter 2) Ingest observer feedback and prior findings | T-04 all Music sections extracted |
| 3 | Synthesis | `synth` | 10 | Draft core.md; Draft adaptation.md; Draft protection.md; Assemble Seed manifest | T-05 manifest schema valid |
| 4 | Cross-Examination | `xexam` | 8 | Reviewer pass on core; Reviewer pass on adaptation and protection; Resolve contradictions; Sign off drafts | T-06 no contradictions between files |
| 5 | Germination Trial | `germ` | 8 | Dry run on micro dataset; Data-swap test on alternate dataset; Output shape check | T-07 dry run completes, T-08 data-swap logic unchanged |
| 6 | Containment | `contain` | 7 | Seed API handshake; Provision isolated sandbox; Upload seed files; Verify upload checksums | T-09 upload checksums match |
| 7 | Planting | `plant` | 8 | ~~Seed v0.1 INIT steps as recorded in `seed-reuse-notes.md` (load data, register rules, warm up)~~ Seed v0.1 INIT (`seed-reuse-notes.md` §3): plant the three layers; heading summary per layer; declared stack listed, not yet verified | T-10 Seed reports ready |
| 8 | ~~Life~~ Seeding & Life | ~~`life`~~ `seeding` | 16 | ~~Seed v0.1 RUNTIME workflows (discovery, assessment, approval, implementation) as recorded in `seed-reuse-notes.md`; each human gate auto-resolved~~ The simulated Seed v0.1 run in Seed's order (D-26): Discovery (gate `servicenow-incident-api` auto-resolved, one timeout recovered); Assessment (License Optimization graded PARTIAL, gate `solution-approval` auto-resolved); Implementation (component built and tested); Cleanup (gate `close-seeding` auto-resolved, four operations, seed consumed); Life (twelve weeks collected, three recalibrations, caught up) | T-11 all gates resolved, T-12 outputs produced |
| 9 | Stress & Probe | `probe` | 9 | Protection rule probes; Malformed input probes; Panel latency measurement | T-13 protection probes, T-14 malformed input rejected, T-15 latency within budget |
| 10 | Harvest Validation | `harvest` | 10 | Collect dashboard payload; Numeric reconciliation; Chart and data consistency; Visual QA; Contrast check | T-16 numeric reconciliation, T-17 chart fitness, T-18 format and label consistency, T-19 palette and layout, T-20 contrast |
| 11 | ~~Cleanup & Report~~ Teardown & Report | `report` | 6 | ~~Seed v0.1 CLOSING_SEEDING;~~ Tear down sandbox; Compile report; Package seed files | T-21 sandbox torn down cleanly |

Sub-step names may be refined in M5, but phase count, order, weights and test ids are fixed unless amended.

*Changed 2026-10-03 (D-26, OQ-11):* Seed v0.1 runs Cleanup before Life and raises no gate in Life, so its Seeding stages, Cleanup and Life all sit in phase 8 in that order, and phase 11 is SeedFoundry's own teardown. Count, order, weights and test ids are unchanged.

### Phase results by iteration (sample Seed)

| Phase | Iteration 1 | Iteration 2 |
|---|---|---|
| 1 to 8 | Passed | Passed |
| 9 Stress & Probe | Findings (L-1) | Passed |
| 10 Harvest Validation | Findings (N-1..N-5, V-1..V-8) | Passed |
| 11 Teardown & Report | Passed | Passed |

## 3. Events

Each event: `{ seq, build_id, iteration, phase, step, type, level, code, message, data, sim_t, wall_ts }`. `sim_t` is simulated seconds since build start (deterministic). `wall_ts` is excluded from determinism tests.

Types: `build.started`, `phase.started`, `step.started`, `log`, `llm.call`, `api.call`, `test.result`, `gate.auto_resolved`, `finding.raised`, `step.completed`, `phase.completed`, `build.completed`, `report.ready`.

*As built (M1):* the same shape carries events outside a build, with `build_id`, `phase`, `step`, `code` and `sim_t` null and `iteration` the current one. M1 added these types: `intake.file_created`, `intake.file_updated`, `intake.file_deleted` (D-32), `build.interrupted` (D-33) and `stream.resync`, which the SSE stream sends when it cannot replay exactly and which is never stored in the log (D-31). The list lives in `backend/seedfoundry/events.py` as `EVENT_TYPES`. *M4:* `demo.reset` (Reset to start, D-46); Load sample Seed and Clear intake emit the intake types.

## 4. Console log format

```
mm:ss.s  LEVEL  message
```

Levels and token colours: `INFO` (text secondary), `LLM` (accent), `API` (info), `TEST` (text primary), `PASS` (success), `WARN` (warning), `FAIL` (danger, the only red).

*As built (M2):* the console has its own tokens, the same in both themes (D-37): `INFO` `--console-text-secondary`, `LLM` `--console-llm`, `API` `--console-api` (the "info" colour; Seed v0.1 has no info token), `TEST` `--console-text`, `PASS` `--console-pass`, `WARN` `--console-warn`, `FAIL` `--console-fail`, timestamps `--console-text-muted`, on `--console-surface`.

Illustrative lines (wording can be refined, tone must stay matter-of-fact, no em dashes):

```
00:00.0  INFO   Build started: iteration 1, seed "License Optimization"
00:00.6  INFO   Inventory: 4 core files, 1 context file, 18.4 KB
00:01.9  TEST   T-03 Ensemble boundary check: 0 findings
00:05.2  LLM    distil music.md: 3,120 tokens in, 640 out (simulated)
00:06.0  INFO   Extracted 4 purpose statements, 11 principles, 7 decision rules
00:14.8  INFO   Drafted core.md (2.1 KB)
00:22.4  INFO   Reviewer: 0 contradictions, 2 clarifications applied
00:27.3  PASS   T-08 Data-swap test: logic unchanged across datasets
00:30.1  API    POST /v0.1/seeds 201 (simulated)
00:31.0  INFO   Sandbox sbx-7f3a provisioned (isolated, no egress)
00:35.6  INFO   Planting: rules registered (simulated Seed v0.1)
00:44.2  INFO   Gate solution-approval auto-resolved from pre-existing knowledge (music.md: Decision Logic)
00:58.7  WARN   Panel "Seats by vendor and product" responded in 4.5 s (budget 1.0 s)
01:04.3  FAIL   N-1 Entitled seats: KPI shows 12,480, product chart sums to 14,976
01:09.9  INFO   Report compiled: 14 findings across 3 categories
```

## 5. Planted defect catalogue (iteration 1)

Applied as an overlay on the polished dashboard: descriptor patches (wrong numbers, wrong chart type, missing labels, artificial delay) plus a scoped stylesheet (`defects.css`, only loaded inside the iteration 1 dashboard). Panel names below are placeholders; in M0 map each defect to the closest real panel of Seed v0.1's License Optimization dashboard and record the mapping in `seed-reuse-notes.md`. *Done in M0 and confirmed (D-28): the binding mapping, panel by panel, is `seed-reuse-notes.md` §5.8. N-3 is checked as the Recoverable KPI against the sum of the recoverable-cost-by-product panel, which is current spend minus optimised spend.* Figures must be derived from the real dataset (e.g. inflation by a fixed factor), not typed in.

### Numeric (checksum) defects

| Id | Panel | Defect | Detected by |
|---|---|---|---|
| N-1 | Licenses by department (bar) | Bars sum to 120% of the KPI total (user example: 100 in data, 120 in chart) | T-16 |
| N-2 | Utilisation distribution | Percentages sum to 112% | T-16 |
| N-3 | Savings KPI | Shown savings do not equal current spend minus optimised spend from the cost panel | T-16 |
| N-4 | License status table | Active + inactive + unassigned does not equal the total in the footer | T-16 |
| N-5 | Vendor table | Total row includes one vendor twice | T-16 |

### Visual defects

| Id | Defect | Detected by |
|---|---|---|
| V-1 | Pie chart with more than 8 slices where a ranked bar chart fits | T-17 |
| V-2 | Red used for a normal (non-fault) series | T-19 |
| V-3 | Off-palette colours; the same category has different colours in two charts | T-19 |
| V-4 | Mixed number formats (1200, 1,200, 1.2k) and missing currency symbol | T-18 |
| V-5 | Missing axis labels and units on at least two charts | T-18 |
| V-6 | Misaligned cards, uneven gutters, one chart overflowing its card, a truncated table | T-19 |
| V-7 | Mixed fonts (one panel title in a system serif) | T-19 |
| V-8 | Muted text below WCAG AA contrast on one panel | T-20 |

### Latency defect

| Id | Defect | Detected by |
|---|---|---|
| L-1 | One panel waits 4.5 s before rendering (spinner shown); budget 1.0 s | T-15 |

Total: 14 findings. The iteration 1 report must list exactly these for the sample Seed (FR-T-6, as amended by D-12 for boundary advisories).

## 6. Validators

### 6.1 Ensemble boundary check (T-03, real)

Rule-based lint over intake text using the boundary table in `ensemble/ensemble_context.md` §6. Examples:

| Rule | Flags |
|---|---|
| B-DATA | Data mappings, schemas, column lists, file paths or raw records outside `environment.md` |
| B-SEC | Security, access or guardrail language in `person.md` or `music.md` |
| B-UI | Colours, themes, layouts, navigation in any file except `environment.md` |
| B-MODEL | Token, context window or model limitation language outside `instrument-awareness.md` |
| B-LOGIC | Prioritisation, scoring or decision rules inside `environment.md` |

Keep rules simple (keyword and pattern sets with a small allowlist) and deterministic. Findings are advisories (D-12): they appear in the report but do not change the verdict. The sample Seed must produce zero.

### 6.2 Numeric reconciliation (T-16, real)

Recompute every figure on the dashboard from the source dataset and compare to the dashboard payload. Checks include: part sums equal totals, percentage sets sum to 100 (tolerance 0.1), derived KPIs equal their formula, table totals equal row sums, the same measure agrees across panels.

### 6.3 Visual QA (T-17 to T-20, real over the descriptor)

Run over the dashboard descriptor plus resolved style values: chart type fitness (pie max 6 slices, categorical comparisons as bars), palette membership (colours must come from chart-role tokens), red reserved for faults, consistent number format per measure, axis labels and units present, card geometry on the grid with equal gutters and no overflow, single font family per role, contrast computed per text/background pair.

### 6.4 Latency (T-15)

Panels declare simulated latency in the descriptor; the server honours it when serving the panel. The probe reads the declared value (deterministic) and compares it to the 1.0 s budget.

## 7. Generated files

All three are generated by templates from distilled intake content (real, deterministic). No em dashes. Each starts with a header block: Seed name, iteration, intake fingerprint (short hash), "Generated by SeedFoundry".

| File | Sections |
|---|---|
| `core.md` | Purpose; Core principles; Value logic; Decision rules; Reasoning approach; Execution guidance; Known issues (only if approved at iteration 1) |
| `adaptation.md` | Operating context; Data sources and mappings; Account and industry adjustments; Presentation notes; Known issues (as above) |
| `protection.md` | Guardrails; Validation checks; Quality controls; Security; Learned rules (iteration 2 only: one rule per resolved iteration 1 finding class, e.g. "Every part-to-whole chart must reconcile to its total"); Known issues (as above) |

## 8. Sample Seed (demo controller: Load sample Seed)

Write four files for the License Optimization domain, consistent with Seed v0.1's data and dashboard, and Ensemble-clean:

- `person.md`: a software asset management and FinOps analyst persona; reasoning methods, how to weigh savings against disruption, evidence standards.
- `instrument-awareness.md`: a generic large language model profile; context budgeting, summarising large license inventories, hallucination risks with figures, always recomputing totals.
- `environment.md`: Data layer describing the dataset fields and sources used by Seed v0.1; UX and Styling layers describing the dashboard; Adaptation for the account and industry; Protection with guardrails and validation checks.
- `music.md`: purpose (reduce license spend without hurting productivity), principles (prioritisation, filtering, confidence, qualification, estimation), value logic, decision logic.
- Optionally one Misc Context file (e.g. vendor contract notes).

Aim for one to two screens of markdown per file. Use real headings matching the Ensemble sections so Assay coverage reads 100%.

*As built (M4):* the files are in `backend/seedfoundry/sample/`: `person.md`, `instrument-awareness.md`, `environment.md`, `music.md` and the Misc Context file `vendor-notes.md` (vendor contract notes), loaded in that order (D-46). Each core file's `##` headings are its Ensemble sections, named as `ensemble/ensemble_context.md` names them: person.md the seven "What belongs here" categories (Domain expertise to Thinking frameworks); instrument-awareness.md Context Management, Model Behaviour (with `###` Strengths, Weaknesses, Failure patterns, Hallucination risks) and Execution Constraints; environment.md Data Layer, User Experience, Styling, Adaptation Layer, Protection Layer; music.md Purpose, Core Principles, Value Logic, Decision Logic. `backend/tests/test_sample.py` checks them against that doc. For M10's routing (D-36), these `##` headings are the sections feedback is appended to; the first heading of music.md is "License Optimization" (OQ-7). music.md also defines what `seed-reuse-notes.md` §5.7 left to it: the class test order (Unassigned, Leaver, Unused, Underused, Active), Underused as active on 1 to 11 days in the last 90 days, Active as 12 or more, and a leaver as an assignee who has left the organisation (`assignee_status` `left` in environment.md's Data Layer). environment.md's Data Layer describes the seat record of §5.7 with its own sources and no Seed v0.1 figures (D-30). The boundary lint is M5's; each file was reviewed by hand against every §6.1 rule (build log, M4).

## 9. Iteration 2 script

Same phases and sub-steps. Differences:

- Assay opens with **Apply observer feedback** (FR-RB-7, FR-RB-8, D-36), before any other sub-step, so everything after it builds from the updated files:
  - *Route feedback to Ensemble files*: one `LLMClient` call (simulated). Logs the segment count and where each went.
  - *Update person.md*, *Update instrument-awareness.md*, *Update environment.md*, *Update music.md*: one sub-step per core file, each appending its routed segments verbatim under `### Observer feedback (iteration 1)` in the matched section. A file that receives nothing still shows its sub-step, completed with "no change".
  - Segments that fit no core file are logged as kept in `observer-feedback-iteration-1.md` only.
  - Illustrative lines (wording refined in M10; figures come from the real routing):

    ```
    00:00.4  LLM    route observer feedback: 6 segments to 4 files (simulated)
    00:00.9  INFO   environment.md: +4 lines in Styling (segments 1, 2)
    00:01.2  INFO   environment.md: +2 lines in Protection (segment 3)
    00:01.5  INFO   music.md: +2 lines in Decision Logic (segment 4)
    00:01.8  INFO   person.md: +1 line in Reasoning methods (segment 5)
    00:02.1  INFO   instrument-awareness.md: +1 line in Hallucination risks (segment 6)
    00:02.4  PASS   Intake updated: 4 files changed, fingerprint 3f9a1c (was 8b20d4)
    ```

  - The boundary check (T-03) then runs on the updated files. Routing by the same rules keeps them clean; a segment that mixes concerns may still raise an advisory, which never changes the verdict (D-12). The demo's prefilled feedback is written to reach all four files and raise none.

- Distillation adds "Ingest observer feedback and prior findings": logs feedback length and the 14 prior findings, then "Planning corrections for all prior findings". It never claims the feedback text mentioned anything it did not (D-5).
- Synthesis logs the learned rules added to protection.md.
- Stress & Probe and Harvest Validation run the same validators against the polished dashboard and pass.
- Report includes "Changes since iteration 1" (FR-R-3).
