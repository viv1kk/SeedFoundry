# SeedFoundry: Build simulation spec

How a build runs: phases, sub-steps, timing, events, logs, planted defects, validators, generated files and the sample Seed. Everything here is deterministic (NFR-1).

## 1. Engine model

- A generator-based **beat engine** (Seed v0.1 pattern, see `seed_docs/implementation-plan.md` and `architecture.md`) walks phases and sub-steps. Each sub-step yields beats; each beat emits one or more events.
- Each phase has a **weight**. Weights sum to 100 and map to a 75 s budget at 1x (range 60 to 90 s allowed). Speed controls scale the clock only.
- All "work" a step reports is produced by real deterministic code where it is cheap to do so (Assay stats, boundary check, file generation, validators) and by `SimulatedLLMClient` / `SimulatedSeedClient` elsewhere.
- RNG: seeded from `sha256(intake content) + iteration`. Used only for cosmetic variety (sandbox id, simulated latencies within fixed bands, token counts jitter).
- State is held server-side; the client receives a snapshot then replays the event log, then streams new events over SSE.

*As built (M5, D-48):* the engine is `backend/seedfoundry/engine/`: `catalogue.py` (phases, weights, sub-steps, tests), `script.py` (each sub-step a generator of beats that returns a one-line summary; the whole script is written when the build starts, as a pure function of the intake, the iteration and the earlier build), `runner.py` (plays the beats on the server's event loop) and `clock.py` (the loop's clock, and `FakeClock` for tests). A phase's beats share its time in proportion to their weights, so `sim_t` is fixed by the script and the build ends at 75.0 s. The runner reads progress from the clock times the speed and waits at most 50 ms at a time; speed and skip change only when beats are played. The RNG is Python's `random.Random` seeded with `sha256("<intake sha256>:<iteration>")`, where the intake sha256 covers every file's category, name and content (the first six hex digits are the fingerprint in logs). The simulated clients are `backend/seedfoundry/clients/` (D-22).

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

*As built (M5):* sub-step names are as in the table, with Planting's refined to Plant the three layers; Heading summary per layer; List the declared stack. In code a sub-step's id is `<phase>.<step>` (`assay.inventory`, `seeding.discovery`, `assay.feedback-route`), in `backend/seedfoundry/engine/catalogue.py`, which a test checks against this table. Each test result is emitted inside the sub-step that computes it, so test ids appear in order T-01 to T-21. What is real, simulated or not yet run in M5 is D-51: real T-01 to T-05, T-09, T-11; simulated T-06, T-07, T-10, T-12, T-21; not run T-08 (until M7) and T-13 to T-20 (until M9), so phases 5, 9 and 10 complete as "incomplete" until then. Synthesis drafts the three layers as outlines (header block and §7's section headings) until M11 fills them; the manifest, upload checksums and Planting's heading summary are computed from those bytes. Planting's declared stack is the bold list items of environment.md's Data Layer (the sample: License Management System (LMS), SAP).

*As built (M7, D-58):* T-08 is real. "Data-swap test on alternate dataset" builds the dashboard payload with the iteration's descriptor and the same query engine on the primary and the alternate estate (D-55), logs a line per estate and one naming the descriptor's digest and whether the two payloads share one structure, and passes when both are structurally valid and their structures match. Germination Trial therefore passes; only Stress & Probe and Harvest Validation are incomplete until M9. "Collect dashboard payload" builds the real payload and logs its panels and seat rows; T-13 to T-20 stay not run (D-57).

*As built (M9, D-62, D-63):* every test runs; none is "not run". **Stress & Probe:** Protection rule probes derives rules from environment.md's Protection layer and evaluates ten probes against them as Seed v0.1's policy evaluation does (T-13; `validators/protection.py`); Malformed input probes feeds the seat record contract every row of the primary estate and eleven malformed rows, and the drill parser three well-formed and five malformed paths (T-14; `validators/records.py`); Panel latency measurement reads each panel's declared latency (T-15). **Harvest Validation:** Collect dashboard payload builds the iteration's dashboard at All products; Numeric reconciliation (T-16), Chart and data consistency (T-17), Visual QA (T-18, T-19) and Contrast check (T-20) run the validators over that payload, the descriptor and the stylesheet it names. The validators run once per build; their problems are grouped into findings (`validators/findings.py`), each raised in the sub-step that finds it, before that test's result. A test with a high finding fails, with medium ones only warns, with none passes. A phase is failed only when a test failed with no finding for it, so phases 9 and 10 complete as findings on iteration 1, as the table below says. Compile report emits `report.ready` (D-64).

*As built (M10, D-67, D-68):* iteration 2's Apply observer feedback sub-steps are real. Route reads the feedback file, makes one routing decision (an `llm.call`, simulated: `intake/routing.py`'s rules decide) and logs where each segment went; each Update sub-step appends the segments routed to its file and the file in Knowledge changes when that sub-step plays; every sub-step after them reads the routed files, and the build's fingerprint is theirs. With the demo feedback, Assay passes with 0 advisories and coverage still 19 of 19.

*As built (M11, D-72):* Synthesis drafts the three files in full (`generate/layers.py`, the M5 outline module renamed), replacing D-51's outlines, so the manifest, the upload checksums and Planting's heading summary are computed from the real files. Each draft sub-step still logs one line ("Drafted core.md: 6 sections, 9,660 bytes"), and Package seed files logs "Seed files packaged: core.md (9,660 bytes), adaptation.md (6,867 bytes), protection.md (1,318 bytes); Approve offers them one by one and as one zip" (summary "3 files packaged"). Approve (D-73) is outside the build: it adds a Known issues section to each file when the approved build has findings, so an approved iteration 2's files are the planted bytes.

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

*As built (M5):* no new types. In a build every event has `build_id`, `iteration` and `sim_t`; every event inside a phase has `phase` (its code id), and every event inside a sub-step has `step`. `code` is the test id (`test.result`), the gate id (`gate.auto_resolved`) or the finding id (`finding.raised`). `build.started` carries the build record (D-49) and `replaces`, the ids of the iteration's earlier build it replaces; `phase.started` and `phase.completed` carry `index`, `name`, and on completion `result` (`passed`, `findings`, `incomplete`, `failed`) and each test's status; `test.result` carries `id`, `name`, `status` (`pass`, `warn`, `fail`, `not_run`), `detail`, `simulated` and, when not run, `arrives_in`; `llm.call` carries `task`, `model`, `tokens_in`, `tokens_out`, `latency_ms`, `simulated`; `api.call` carries `method`, `path`, `status`, `latency_ms`, `simulated`, `response`; `build.completed` carries the test counts, finding and advisory ids, gates and `sim_seconds`. `report.ready` is not emitted until M9 (D-51). A sample iteration 1 build is 220 events. Speed and skip emit no event (D-48).

*As built (M6, D-54):* the build record (and so `build.started`'s `data.build`) also carries `sim_seconds`, the build's simulated length (75.0), so the Build page reads progress as `sim_t / sim_seconds`. No event changed.

*As built (M7, D-58):* no new types. T-08's sub-step emits three log lines before its result, so a sample iteration 1 build is 223 events (was 220).

*As built (M9, D-62 to D-64):* no new types; `report.ready` is now emitted, once, inside Compile report (phase 11), with the verdict, the counts and the finding ids by category; it is not the last event, because every event of a build sits in a sub-step or is its first or last (`build.started`, `build.completed`). A dashboard `finding.raised` carries `id`, `category`, `test`, `checks`, `panel`, `panels`, `panel_titles`, `expected`, `shown`, `severity`, `phase`, `step`, `message`, `catalogued`, `advisory` (false) and `problems` (each validator problem behind it); `code` is the finding id; level FAIL for a high finding, WARN for medium. `test.result` no longer carries `arrives_in`. `phase.completed` names a findings phase's ids ("Harvest Validation: findings (N-1, ..., V-8)") and a failed phase's unexplained tests. `build.completed` also carries `verdict` (`id`, `label`, `tone`). The report is `GET /api/builds/{id}/report`, assembled from the kept log. A sample iteration 1 build is 256 events (was 223); iteration 2 is 264.

*As built (M10, D-67, D-68):* no new types. The rebuild's single change emits `intake.file_created` (or `intake.file_updated`) for `observer-feedback-iteration-1.md`, `source: "rebuild"`, then `build.started`, after one save. Each Update sub-step that changes a file is followed, in the same save, by one `intake.file_updated` (`source: "feedback"`, `changed: ["content"]`) in the intake shape: no `build_id`, `phase`, `step` or `sim_t`, so it is not in the build's kept log or its console. Route's lines carry `segment`, `file`, `section` and `matched` (or `kept`); each Update line carries `file`, `file_id`, `section`, `segments`, `lines_added` and `created`. The build record keeps `files`, the intake it read (D-67), which the snapshot and `build.started` leave out. With the demo feedback, iteration 2 is 278 events (was 264); iteration 1 is unchanged at 256.

*As built (M11, D-72, D-73):* no build event added or removed: iteration 1 is still 256 events and iteration 2 (the demo feedback) 278. One new type outside any build, `seed.approved` (Approve): no `build_id`, `phase` or `sim_t`, so no build log or console holds it; it carries the iteration, the build id, the Seed name, each file's bytes and sha256, and the known issue ids. Reset clears the approval with `demo.reset`. The list lives in `events.py` as `SEED_EVENT_TYPES`.

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

*As built (M5):* the engine writes each event's `level` and `message`; the console itself is M6's. The sample's iteration 1 build reads, for example:

```
00:00.0  INFO   Build started: iteration 1, seed "License Optimization"
00:00.0  INFO   Inventory: 4 core files, 1 context file, 16.8 KB
00:03.6  PASS   T-03 Ensemble boundary check: 0 findings
00:05.8  LLM    distil music.md: 910 tokens in, 572 out (simulated)
00:07.2  INFO   Extracted 3 purpose statements, 17 principles, 4 value statements, 7 decision rules
00:33.6  API    POST /v0.1/seeds 201 (simulated)
00:34.9  INFO   Sandbox sbx-7d38 provisioned (isolated, no egress, simulated)
00:48.0  INFO   Gate solution-approval (approval) auto-resolved: approve License Optimization at potential PARTIAL. Basis: music.md, Decision Logic
01:04.2  TEST   T-16 Numeric reconciliation: not run, this validator arrives in M9
01:15.0  INFO   Build completed: 12 tests passed, 9 not run; 0 findings, 0 boundary advisories
```

*As built (M7, D-58):* the data-swap lines and the end of the sample's iteration 1 build now read:

```
00:28.7  INFO   Primary estate: 13,050 seats, 17 products, 10 vendors; payload for 11 panels, 0 structural problems
00:29.5  INFO   Alternate estate: 5,620 seats, 11 products, 8 vendors; payload for 11 panels, 0 structural problems
00:30.4  INFO   Same descriptor (abcc42) and query engine on 2 estates; payload structure identical
00:31.2  PASS   T-08 Data-swap logic unchanged: same descriptor and query engine on both estates, both payloads structurally valid
01:03.0  INFO   Collected the License Optimization payload (polished): 11 panels at All products, from 13,050 seat rows in the primary estate
01:15.0  INFO   Build completed: 13 tests passed, 8 not run; 0 findings, 0 boundary advisories
```

*As built (M8, D-60):* the payload line no longer names the variant, so a build does not announce its own defects before M9's validators find them: "Collected the License Optimization payload: 11 panels at All products, from 13,050 seat rows in the primary estate". Iteration 1's descriptor digest in the data-swap line is now that of the rough descriptor (`e6a28a`); iteration 2's is still `abcc42`. Event and line counts are unchanged.

*As built (M9, D-62, D-63):* the sample's iteration 1 build now ends:

```
00:56.2  INFO   Protection rules from environment.md, Protection Layer: 9 rules from 4 lines
00:56.7  INFO   PB-1 remove an Unused seat from the License Management System: DENY by P-3 (environment.md, Protection Layer, line 122)
00:59.2  PASS   T-13 Protection probes: 10 of 10 probes as expected: 6 denied by Protection rules, 3 allowed, 1 denied by the default rule for a missing fact
01:01.2  PASS   T-14 Malformed input rejected: 16 of 16 malformed inputs refused; 13,050 seat rows and 3 drill paths accepted
01:02.2  WARN   L-1 Panel "Seats by vendor and product" responds in 4.5 s (budget 1.0 s)
01:02.5  WARN   T-15 Latency within budget: 1 finding (L-1) from 1 problem
01:03.0  WARN   Stress & Probe: findings (L-1)
01:03.9  FAIL   N-1 Entitled seats: KPI shows 13,050, product chart sums to 15,660; 18 problems in all
01:05.0  FAIL   T-16 Numeric reconciliation: 5 findings (N-1, N-2, N-3, N-4, N-5) from 38 problems
01:08.2  WARN   V-3 Seats by vendor and product: Unused drawn in #5470c6, which is not a palette token; 2 problems on 2 panels
01:10.5  WARN   Harvest Validation: findings (N-1, N-2, N-3, N-4, N-5, V-1, V-2, V-3, V-4, V-5, V-6, V-7, V-8)
01:13.3  INFO   Report compiled: 14 findings across 3 categories; verdict Completed with findings
01:15.0  WARN   Build completed: 15 tests passed, 5 warned, 1 failed; 14 findings, 0 boundary advisories; verdict Completed with findings
```

Iteration 2 ends "Report compiled: 0 findings; verdict Passed" and "Build completed: 21 tests passed; 0 findings, 0 boundary advisories; verdict Passed". The console shows 168 lines of 256 events for iteration 1 (was 135 of 223) and 164 of 264 for iteration 2. Iteration 2's Distillation now reads "Prior findings from iteration 1: 14" and "Planning corrections for all 14 prior findings", and Synthesis "Learned rules for protection.md: 3 rules, one per finding class (Latency, Numeric, Visual)" (D-52). A warned test is no longer counted as passed in the completion line (D-63).

*As built (M10, D-68):* the sample's iteration 2, rebuilt with the demo feedback, opens:

```
00:00.0  INFO   Build started: iteration 2, seed "License Optimization"
00:00.0  INFO   Read observer-feedback-iteration-1.md: 10 segments, 1,757 bytes
00:00.1  LLM    route observer feedback: 453 tokens in, 102 out (simulated)
00:00.6  INFO   Segment 1 to environment.md, Data Layer: totals, add up, shares, twice, records
00:00.7  INFO   Segment 2 to environment.md, Styling: pie, slices, bar chart
00:01.0  INFO   Segment 6 to environment.md, User Experience: spinner, seconds, panel, waiting
00:01.1  INFO   Segment 7 to instrument-awareness.md, Model Behaviour: Hallucination, language model, the model
00:01.2  INFO   Segment 8 to person.md, Reasoning methods: reasoning, assumption, evidence, conclusion
00:01.3  INFO   Segment 9 to music.md, Value Logic: saving, value, success
00:01.4  INFO   Segment 10 kept in observer-feedback-iteration-1.md only: it fits no Ensemble file
00:01.5  INFO   Routed 9 of 10 segments to 4 files; 1 kept in observer-feedback-iteration-1.md only
00:01.6  INFO   person.md: +4 lines in Reasoning methods (segment 8)
00:01.8  INFO   instrument-awareness.md: +4 lines in Model Behaviour (segment 7)
00:02.0  INFO   environment.md: +10 lines in Styling (segments 2, 3, 4, 5)
00:02.1  INFO   environment.md: +4 lines in User Experience (segment 6)
00:02.3  INFO   environment.md: +4 lines in Data Layer (segment 1)
00:02.5  INFO   music.md: +4 lines in Value Logic (segment 9)
00:02.6  INFO   Intake updated: 4 files changed, fingerprint 49616b (was 6bb2d9)
00:02.8  INFO   Inventory: 4 core files, 2 context files, 20.3 KB
00:04.1  PASS   T-03 Ensemble boundary check: 0 findings
```

The console shows 178 lines of 278 events for iteration 2 (was 164 of 264); iteration 1 is unchanged (168 of 256). The summary line is INFO, not the illustrative PASS, as no test stands behind it.

Gate lines use Seed v0.1's ids (`seed-reuse-notes.md` §4.2), never "H-02". A test not yet run is level TEST, so it reads as neutral, not as a warning (D-51).

*As built (M6, D-54):* the console is `frontend/src/components/build/BuildConsole.vue`. Every build event is a line except `step.started` and `step.completed`, which the stepper shows, so the sample's iteration 1 is 132 lines of 220 events. *M7 (D-58):* 135 lines of 223 events. *M9:* 168 lines of 256 events (iteration 2: 164 of 264). Tenths are floored (`74.182` is `01:14.1`), and an event without `sim_t` (`build.interrupted`) is stamped `--:--.-`. The level filter's TEST button also shows PASS lines, and INFO lines show only under All.

*As built (M11, D-72):* the console is unchanged at 168 lines for iteration 1 and 178 for iteration 2. Synthesis and Teardown now read, for the sample's iteration 2:

```
00:15.0  INFO   Drafted core.md: 6 sections, 10,216 bytes
00:17.0  INFO   Drafted adaptation.md: 4 sections, 8,218 bytes
00:19.0  INFO   Drafted protection.md: 5 sections, 2,918 bytes
00:19.5  INFO   Learned rules for protection.md: 3 rules, one per finding class (Latency, Numeric, Visual)
01:14.1  INFO   Seed files packaged: core.md (10,216 bytes), adaptation.md (8,218 bytes), protection.md (2,918 bytes); Approve offers them one by one and as one zip
```

Cross-Examination's simulated token counts read the drafts, so they grew with them.

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

*As built (M8, D-60):* the overlay is `backend/seedfoundry/dashboard/overlay.py`: fourteen patches, each tagged with its defect id, in three layers. Descriptor patches (V-1 to V-5, L-1) make iteration 1's descriptor (`variant` `rough`, which also names `defects.css` and its root class `defects-overlay`); payload rules (N-1 to N-5) rewrite the figures the query engine computed, by fixed rules over the true figures and the same rows, so they apply at any drill level; `frontend/src/styles/defects.css` (V-6 to V-8) is loaded only when a descriptor names it, and every rule sits under the root class. The rules, what each shows and where some fall away at a deep drill level are in `seed-reuse-notes.md` §5.8. Iteration 2 is M7's polished dashboard unchanged. Findings are M9's: the build still reads "13 tests passed, 8 not run".

*As built (M9, D-63):* the validators find the catalogue: `validators/findings.py` maps problems to these ids by test, check and panel (T-16 by panel; V-1 to V-8 by check; L-1 by T-15), never by reading the overlay, and several problems make one finding. The sample's iteration 1 build raises exactly the fourteen (the D-14 test), iteration 2 none, and removing any one overlay patch, the stylesheet's included, removes exactly its finding from the build (`backend/tests/test_findings.py`). Severity: Numeric high, Visual and Latency medium (OQ-26). A problem no entry owns would be raised as N-X1, V-X1 or L-X1; the sample raises none.

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

*As built (M5, D-50):* `backend/seedfoundry/intake/boundary.py`. Only the four core files are checked. Each pattern carries its suggested home (B-DATA: environment.md, Data Layer; B-SEC: environment.md, Protection Layer; B-UI: environment.md, Styling or User Experience; B-MODEL: instrument-awareness.md; B-LOGIC: music.md, Core Principles or Decision Logic). One finding per rule per line, id `<rule>-<n>`. The allowlist holds Seed v0.1's panel title "Optimisation candidates" (either spelling); without it the sample's environment.md would raise one B-LOGIC advisory. The sample gives zero.

### 6.2 Numeric reconciliation (T-16, real)

Recompute every figure on the dashboard from the source dataset and compare to the dashboard payload. Checks include: part sums equal totals, percentage sets sum to 100 (tolerance 0.1), derived KPIs equal their formula, table totals equal row sums, the same measure agrees across panels.

*As built (M7, D-57):* `backend/seedfoundry/validators/numeric.py` `reconcile(payload, dataset)`, minimal but real: it recounts from the seat rows with its own loops (not the query engine) and checks each KPI against its formula, the per-product bars against the KPIs, treemap cells and parents, the legend's shares (sum within 0.1 of 100, each within 0.1), the trend per month, recoverable cost per product and the KPI against their sum, the candidates' rows and total row, the Seats footer and the rows on the page. It passes on the polished payload at every drill level of the primary estate and at the root of the alternate (tests), and catches each kind of break M8 plants. Not yet run in the build: T-16 is not run until M9. *M8 (D-60):* when two panels disagree on one measure, the problem names the panel whose figure is off its recount, so N-3's wrong KPI is not blamed on the candidates table; on iteration 1 it finds N-1 to N-5 and nothing else. *M9 (D-63):* runs in the build as T-16 over the iteration's payload at All products. Each problem's message reads on its own with its figures ("Entitled seats: KPI shows 13,050, product chart sums to 15,660", "Seats footer: Total shows 12,401, the class counts sum to 13,050"), and problems carry a unit, so expected and shown read as counts, money or shares.

### 6.3 Visual QA (T-17 to T-20, real over the descriptor)

Run over the dashboard descriptor plus resolved style values: chart type fitness (pie max 6 slices, categorical comparisons as bars), palette membership (colours must come from chart-role tokens), red reserved for faults, consistent number format per measure, axis labels and units present, card geometry on the grid with equal gutters and no overflow, single font family per role, contrast computed per text/background pair.

*As built (M7, D-57):* `backend/seedfoundry/validators/visual.py` `check(descriptor, payload)` over the descriptor and the token values of `frontend/src/styles/tokens.css` in both themes: T-17 (pie slices, categorical comparisons as bars), T-18 (one format per measure per context, currency, axis names, value-axis units), T-19 (token palette, one role per class, red for the Leaver class only, spans packing the twelve-column grid with one gutter and one height per chart row, the first chart full width, one family per font role) and T-20 (text at 4.5:1 and chart roles at 3:1 on the panel surface). The polished descriptor passes; each rule catches a planted break (tests). The CSS side of V-6 to V-8 (geometry, fonts and contrast as `defects.css` applies them) is M8's and M9's. Not yet run in the build: T-17 to T-20 are not run until M9. *M8 (D-60):* `check` also reads a pie's slice roles and a panel's own class colours, counts a pie's slices as its non-null values, and checks the rules of the stylesheet the descriptor names (`validators/styles.py`, a minimal reader): a card moved off the grid, an element wider than its card, clipped table text, a font family that is not a font token (T-19), and text colours on the panel surface in both themes (T-20). On iteration 1 it finds V-1 to V-8 and nothing else; iteration 2 is clean. *M9 (D-63):* runs in the build as T-17 to T-20. Every message starts with the panel's title; a format problem shows the panel's own figure in both formats ("13050 (plain)" against "13,050 (count)"), and a stylesheet rule's target is named in words ("the title", "the last two columns").

### 6.4 Latency (T-15)

Panels declare simulated latency in the descriptor; the server honours it when serving the panel. The probe reads the declared value (deterministic) and compares it to the 1.0 s budget.

*As built (M8, D-60):* the browser honours it, not the server. The server answers the whole dashboard in one request (D-56), so a server-side wait would hold every panel; instead `ChartPanel` waits the declared `latency_ms` before drawing, with a spinner, while every other panel draws at once (NFR-3). Only iteration 1's treemap declares one (4,500 ms). It waits on first draw, on reload and on each drill, not on paging or sorting the Seats table (OQ-25). The probe is `backend/seedfoundry/validators/latency.py` `check(descriptor)`, which reads the declared value against the 1.0 s budget; it is not run in the build until M9. *M9:* it runs in Panel latency measurement as T-15, and its message reads `Panel "Seats by vendor and product" responds in 4.5 s (budget 1.0 s)`.

### 6.5 Protection and malformed input probes (T-13, T-14)

*As built (M9, D-62):* not in the original spec beyond §2's sub-step names. **T-13:** `validators/protection.py` derives rules (P-1, P-2, ...) from environment.md's Protection layer by fixed line patterns (read only; never removes or changes a seat; cost only where a unit price exists; names only at the seat level, never in exports; data stays inside the sandbox) and evaluates ten fixed probes (PB-1 to PB-10) against them as Seed v0.1 does (seed-reuse-notes.md §2.6): the strictest effect of the matching rules wins, the most specific is cited, a missing fact or no allowing rule falls to the default DENY. Pass: every probe as expected from a stated rule (PB-5 expects the default). Warn: a probe decided only by the default rule, or an allowed request denied. Fail: a request the layer should stop is allowed. The sample: 9 rules from 4 lines, pass. **T-14:** `validators/records.py` checks a seat record against the contract of environment.md's Data Layer (fields, `LIC-` id, known product, status, twelve usage counts of 0 to 31 days, dates, and the class music.md's rules give); every row of the estate must pass and eleven malformed rows must fail, and the query engine's drill parser must refuse five malformed paths and accept three. Fail when a malformed input is accepted; warn when a well-formed one is refused. Neither raises a finding (OQ-27).

## 7. Generated files

All three are generated by templates from distilled intake content (real, deterministic). No em dashes. Each starts with a header block: Seed name, iteration, intake fingerprint (short hash), "Generated by SeedFoundry".

| File | Sections |
|---|---|
| `core.md` | Purpose; Core principles; Value logic; Decision rules; Reasoning approach; Execution guidance; Known issues (only if approved at iteration 1) |
| `adaptation.md` | Operating context; Data sources and mappings; Account and industry adjustments; Presentation notes; Known issues (as above) |
| `protection.md` | Guardrails; Validation checks; Quality controls; Security; Learned rules (iteration 2 only: one rule per resolved iteration 1 finding class, e.g. "Every part-to-whole chart must reconcile to its total"); Known issues (as above) |

*As built (M11, D-72 to D-74):* `backend/seedfoundry/generate/layers.py` writes the three files in Synthesis; `backend/seedfoundry/package.py` approves, adds Known issues and zips.

- **Header block:** `# <Seed>: <file>`, then `- Seed:`, `- Iteration:`, `- Intake fingerprint:` (six hex digits) and `- Generated by SeedFoundry`, then one line on what the layer holds ("Core layer: what this Seed is for, what it values, and how it decides, reasons and works."). Then the sections above, in order; a section the intake does not state reads "Nothing is stated for this section."
- **What goes where** (project-notes §4, never stated in a file or on screen, D-9): core.md's Purpose is music.md's lead and Purpose; Core principles, Value logic and Decision rules are its Core Principles, Value Logic and Decision Logic; Reasoning approach is person.md's lead and every section; Execution guidance is instrument-awareness.md's. adaptation.md's Operating context is environment.md's lead and each Misc Context note under its own title (not the observer feedback); Data sources and mappings is the Data Layer; Account and industry adjustments the Adaptation Layer; Presentation notes User Experience and Styling. protection.md takes the Protection Layer's sub-sections by their titles: Security, Quality controls, Validation checks, and Guardrails for the rest.
- **Text** is copied as written; headings move to sit under the layer's section, never inside a code fence. A mention of an intake file by name becomes the layer or note holding that text now (the sample's "as music.md defines them" reads "as core.md defines them", "see vendor-notes.md" reads "see Vendor contract notes"), so no file names a Knowledge file.
- **Iteration 2** reads the routed files build 2 keeps, so each `### Observer feedback (iteration 1)` sits in the layer of its section: Reasoning approach, Execution guidance and Value logic in core.md, Data sources and mappings and Presentation notes in adaptation.md.
- **Learned rules** (iteration 2): "One rule for each class of finding iteration 1 raised. ...", then a `###` per class in report order, from iteration 1's kept findings (the same data as Synthesis's line): Numeric "Every part-to-whole chart must reconcile to its total. ...", Visual "Every chart must keep to the design system. ...", Latency "Every panel must render within its 1.0 s budget. ...", each ending "Learned from iteration 1's N-1 (Entitled, assigned and active by product), ..." with the findings it came from.
- **Known issues** (added at Approve, when the approved build has open findings, advisories never, OQ-31): "Approved at iteration 1 with 14 open findings. Each stays a known issue until a later build resolves it.", then one item per finding: id, category, severity, message, expected and shown, and the panels when there are several. The same list in all three files.
- **Sizes** for the sample: iteration 1 approved core.md 12,493, adaptation.md 9,700 and protection.md 4,151 bytes; iteration 2 approved 10,216, 8,218 and 2,918. Golden copies are `backend/tests/golden/seed/iteration-<n>/`.

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

*As built (M5, D-52):* routing is M10's, so until then the Apply observer feedback sub-steps read the feedback file and count its segments, route nothing, and say so: "Routing feedback to the Ensemble files arrives in M10, so no segment was routed", then "<file>: no change, no feedback was routed to it" for each core file and "Intake unchanged: 0 files changed, fingerprint <x>". Distillation counts prior findings from iteration 1's kept log (0 until M9's validators raise them). Iteration 2 is started in M5 by API only (`POST /api/builds` with `{"iteration": 2}`, D-49).

*As built (M10, D-67 to D-69), replacing D-52's note above:* routing is real (`backend/seedfoundry/intake/routing.py`). **Segments** are `feedback.py`'s paragraphs and list items. **Targets**, in D-36's order: environment.md Styling, User Experience, Data Layer, Protection Layer; instrument-awareness.md Model Behaviour; person.md Reasoning methods; music.md Core Principles, Decision Logic, Value Logic; each is the boundary lint's patterns for that home plus a few words for homes the lint never checks. A segment scores a point per matching pattern; the highest wins, a tie goes to the earlier target, no match keeps it in the feedback file only. **Edits:** appended verbatim at the end of the `##` section under `### Observer feedback (iteration 1)` (created if missing; a missing section is added at the end of the file); a segment already there is not added again. **Lines** are the ones in §4's M10 note: Route logs the read, one `llm.call` "route observer feedback" (simulated), a line per segment with the words it matched, and a summary; each Update sub-step logs a line per section it changed with the lines added (or "no change, no feedback was routed to it") and completes with "+n lines in <section>" (or "no change"); the last logs "Intake updated: n files changed, fingerprint <new> (was <old>)". The files really change as each Update plays (`intake.file_updated`), and iteration 1's versions stay with build 1 (`GET /api/builds/{id}/files`). The demo feedback (`backend/seedfoundry/sample/rebuild/observer-feedback-iteration-1.md`, Prefill's text) routes 9 of 10 segments to all four files and raises no advisory. **Iteration 2 starts** only by the rebuild: `POST /api/builds` with `{"iteration": 2, "feedback": "..."}` saves the feedback file and starts the build in one change (D-67). Distillation still reads "Prior findings from iteration 1: 14" and "Planning corrections for all 14 prior findings", and Synthesis "Learned rules for protection.md: 3 rules, one per finding class (Latency, Numeric, Visual)"; neither claims what the feedback said (D-5). The report's "Changes since iteration 1" is D-69's.

*As built (M11, D-72):* Synthesis's learned rules line now has a file behind it: protection.md's Learned rules section holds one rule for each class the line names, from the same iteration 1 findings (a test checks the two agree).
