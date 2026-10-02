# Systems --- V1 Requirements

> **Status:** Agreed baseline, met as built. All milestones, M0 to M22,
> are built, and the as-built state was reviewed against this document
> and accepted as final on 2026-10-02 (`decisions.md` §8). The product is
> displayed as **Seed v0.1**.
>
> **Related documents:**
> `project-notes.md` --- vision and product context (§§1--82). Aspirational;
> describes the eventual agentic system.
> `implementation-plan.md` --- how these requirements were built.
> `decisions.md` --- rulings on open decisions, and the amendments A-1 to
> A-16 applied below.
> `architecture.md`, `design-system.md`, `operator-guide.md` --- the
> system, the visual language and the presenter's procedure, as built.
>
> Where this document and `project-notes.md` §§1--82 disagree, **this
> document wins**. References of the form (§N) point back to the vision
> document for rationale.
>
> **Amended 2026-09-23** by the Seeding and Life rework (the Alex
> Prigojine session; `decisions.md` §7, D-11 to D-17, A-3 to A-9). The
> interface now uses a display vocabulary that differs from the one used
> in these requirements: see §5.13. The requirements keep their original
> terms, such as *solution* and *feasibility*, because those are also the
> code's terms (D-11). Superseded requirements are struck through and
> left in place.

---

## 1. Purpose and context

V1 is a **visually polished, fully deterministic simulation** of a
methodology-driven autonomous enterprise analytical system.

It demonstrates the behaviour and architecture of the eventual product
without implementing real enterprise integration, autonomous agents, or
cloud deployment.

The demo narrative runs: plant a seed → discover a client environment →
assess analytical feasibility → escalate decisions to a human → build
approved solutions → run them → explore results down to underlying
evidence.

**The audience is a viewer being shown the system.** Every requirement
below exists to make that viewing experience credible and inspectable.

---

## 2. Goals

| ID   | Goal                                                                                                                       |
| ---- | -------------------------------------------------------------------------------------------------------------------------- |
| G-1  | Demonstrate that the system is driven by an explicit **methodology**, not by prompting a model (§69, §71).                    |
| G-2  | Show the system building an understanding of an initially **unknown environment** (§15).                                     |
| G-3  | Show that autonomy exists inside **hard governance boundaries** the viewer can inspect (§9, §10).                            |
| G-4  | Show humans as **decision authorities at meaningful boundaries**, not approvers of every step (§74).                         |
| G-5  | Produce conclusions that **trace back to underlying data**, with no unexplained assertions (§23, §35, §72).                   |
| G-6  | Deliver a genuinely **interactive analytical application**, not a static report (§31, §32).                                  |
| G-7  | Prove an architecture where each simulated subsystem can later be **replaced by a real one without rewriting the UI** (§41, §75). |
| G-8  | Run **reliably and identically** every time it is demonstrated (§45).                                                        |

### Non-goals

V1 is explicitly not a chatbot, a RAG application, a static BI dashboard,
a CRUD application, or a collection of fake AI agents (§70).

---

## 3. Scope

### 3.1 Built for real

- User interface, in full
- Lifecycle state machine
- Event generation, streaming, and replay
- Seed file upload, validation, and heading-level parsing
- Human-in-the-loop interaction and escalation
- Policy evaluation (genuinely evaluative, not scripted)
- Solution lifecycle and state transitions
- Deterministic analytical datasets
- Aggregation, filtering, cross-filtering, drill-down
- Evidence computation
- Dashboard rendering and chart interaction

### 3.2 Simulated

- Enterprise discovery and network scanning
- All system connections (ServiceNow, SAP, SQL Server, License
  Management, Legacy Registry)
- Credential validation
- Agent reasoning
- Code generation
- Model training
- Build, test execution, and deployment

The boundary between §3.1 and §3.2 must remain legible in the code
structure (§63).

---

## 4. Out of scope

### 4.1 Excluded from V1

| Area                  | Excluded                                                                 |
| --------------------- | ------------------------------------------------------------------------ |
| Intelligence          | Any LLM or inference, anywhere, in any phase                             |
| Seed                  | Seed **content** driving system behaviour; knowledge compilation         |
| Integration           | Real connectors, real credentials, real network access                   |
| Lifecycle             | Evolution phase. *Clarified by A-8:* recalibrating baselines within a run, as the Life pane does (FR-LF6), is not Evolution. Evolution means changing methodologies, components or code. |
| Persistence           | Durable state, pause/resume, resume after restart                        |
| Packaging             | Docker, containerisation, hosted deployment                              |
| Build phase           | Generated source-code artifacts shown to the viewer                      |
| Failure handling      | Failure-injection mode beyond the single scripted timeout                |
| Platform              | Authentication, multi-user, multi-client, distributed infrastructure     |

### 4.2 Deliberately discarded from the vision document

- **§19's discovery totals** ("7 Systems / 14 Data Sources / 31 Relevant
  Datasets"). The environment contains exactly the five systems named in
  §42; reported counts are computed from what actually exists.
- **§29's Docker requirement**, replaced by a single-command local
  launcher.
- **§71's LLM seams**, recorded as future work only.

---

## 5. Functional requirements

### 5.1 Seed and initialization --- `FR-S`

| ID     | Requirement                                                                                                                                                  |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| FR-S1  | The repository ships three genuine seed files --- `core.md`, `adaptation.md`, `protection.md` --- containing real methodology, mapping and policy content.      |
| FR-S2  | The INIT screen presents the three layers as a deliberate "plant the seed" gesture, not a generic file uploader (§12, §48).                                    |
| FR-S3  | All three layers must be supplied before initialization can proceed.                                                                                          |
| FR-S4  | The loader validates each file is present and parseable as Markdown, and rejects it otherwise with a clear reason.                                             |
| FR-S5  | The loader parses each file's **heading structure** and displays a per-layer "loaded / parsed" summary derived from it (§67). This summary is genuinely derived from file content. |
| FR-S6  | Seed file content **must not** alter system behaviour. Methodologies, feasibility outcomes and policy rules are fixed regardless of what is uploaded.          |
| FR-S7  | A hidden operator affordance loads the bundled seed files without using a file picker.                                                                        |

### 5.2 Lifecycle and state --- `FR-L`

| ID     | Requirement                                                                                                                                       |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| FR-L1  | The system implements a formal state machine with an explicit transition table, not scattered boolean flags (§59).                                  |
| FR-L2  | ~~States: `UNINITIALIZED`, `INITIALIZED`, `DISCOVERING`, `DISCOVERY_BLOCKED`, `DISCOVERY_COMPLETE`, `ASSESSING`, `AWAITING_APPROVAL`, `IMPLEMENTING`, `IMPLEMENTATION_COMPLETE`, `READY_TO_RUN`, `RUNNING` (§58).~~ **Superseded by FR-L9** (A-3). |
| FR-L3  | An attempted illegal transition raises an error rather than mutating state.                                                                        |
| FR-L4  | Blocking on human input is represented as a flag (`blockedOn`) alongside the current state, not as a separate state per phase.                      |
| FR-L5  | System State is the sole source of truth. Simulated agents read from and write to it; they never hold authoritative state internally (§37, §73).     |
| FR-L6  | A persistent lifecycle indicator shows completed, current and future phases at all times (§14). *Superseded by FR-G1 under A-4, then restored by A-10 (D-18): the lifecycle strip is the Seeding pane's indicator.* |
| FR-L7  | State is held in memory for a single run. An explicit Reset returns the system to `UNINITIALIZED`.                                                  |
| FR-L8  | ~~From `READY_TO_RUN`, the user can run any ready solution, return to the workspace, and run another. Completion is per-solution, not global.~~ **Superseded by FR-L10** (A-5). |
| FR-L9  | States: FR-L2's eleven, plus `CLOSING_SEEDING` between `IMPLEMENTATION_COMPLETE` and `READY_TO_RUN`. The edge `IMPLEMENTATION_COMPLETE → READY_TO_RUN` is replaced by `IMPLEMENTATION_COMPLETE → CLOSING_SEEDING → READY_TO_RUN`. `CLOSING_SEEDING` belongs to the Implementation phase (D-16). |
| FR-L10 | From `READY_TO_RUN`, the user can run any ready solution, return to the Life pane's list of solutions, and run another. Completion is per-solution, not global (D-14). |

### 5.3 Event stream --- `FR-E`

| ID     | Requirement                                                                                                                                     |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| FR-E1  | All system activity is expressed as events. The UI reacts to the event stream rather than knowing how agents work (§38).                          |
| FR-E2  | Events are delivered to the frontend over SSE.                                                                                                  |
| FR-E3  | Every event carries a monotonic sequence number, timestamp, machine-readable `type`, `phase`, display `category`, `severity` and `message`.       |
| FR-E4  | Display categories: `DISCOVERY`, `ANALYSIS`, `VALIDATION`, `DECISION`, `POLICY`, `WARNING`, `SUCCESS`, `HUMAN_INPUT` (§16).                        |
| FR-E5  | The frontend fetches a full state snapshot on connect, then applies events from that snapshot's sequence number onward.                           |
| FR-E6  | A detected sequence gap causes the frontend to discard local state and re-snapshot.                                                              |
| FR-E7  | Reconnection replays missed events exactly, from the retained event log.                                                                        |
| FR-E8  | The activity stream presents events as an **auditable activity stream**, not a developer terminal (§16).                                          |
| FR-E9  | Events report operational facts and decision-relevant reasons only. No simulated internal reasoning or chain-of-thought is displayed (§16).       |

### 5.4 Discovery --- `FR-D`

| ID     | Requirement                                                                                                                             |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| FR-D1  | The mock environment contains exactly five systems: ServiceNow, SAP, SQL Server, License Management System, Legacy Application Registry (§42). |
| FR-D2  | Each system expands during discovery into its constituent services, APIs, databases and datasets (§50).                                   |
| FR-D3  | The environment is rendered as a graph whose nodes appear progressively as they are discovered (§15).                                     |
| FR-D4  | Node statuses: `unknown`, `detected`, `testing`, `validated`, `requires-input`, `connected`, `error` (§50).                               |
| FR-D5  | Edge kinds: `contains`, `connects_to`, `provides`, `depends_on` (§50).                                                                   |
| FR-D6  | The Legacy Application Registry is presented as administrator-supplied rather than automatically discovered (§8, §19).                    |
| FR-D7  | Discovery pauses for a scripted credential request and resumes on submission (§68).                                                       |
| FR-D8  | Discovery includes exactly one technical failure --- an endpoint timeout --- which the system retries and recovers from.                  |
| FR-D9  | On completion, the system reports counts of systems, data sources and datasets **computed from the constructed graph**, never authored.    |
| FR-D10 | Discovery completion displays per-system connection status and which methodologies appear feasible (§19).                                |

### 5.5 Protection layer --- `FR-P`

| ID     | Requirement                                                                                                                                 |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| FR-P1  | Policy enforcement is implemented as an evaluative engine that matches requested actions against a rule set. It is not scripted output (§10). |
| FR-P2  | Every simulated agent action requiring a capability passes through the policy engine before proceeding.                                      |
| FR-P3  | Decision effects: `ALLOW`, `DENY`, `ESCALATE` (§62).                                                                                         |
| FR-P4  | Policy decisions appear inline in the activity stream as first-class events, citing the action, resource, effect and rule id.                 |
| FR-P5  | A dedicated Protection panel displays the active rule set, running counts of allowed / denied / escalated requests, and a filterable audit log. |
| FR-P6  | The demo includes at least one `DENY` and one `ESCALATE` decision, so the layer is visibly a boundary rather than a formality.                |
| FR-P7  | The rule set shown in the UI corresponds to the rules documented in `protection.md`.                                                          |

### 5.6 Human-in-the-loop --- `FR-H`

| ID     | Requirement                                                                                                                                   |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| FR-H1  | The human input surface appears only when input is required, and disappears once resolved. It does not permanently occupy screen space (§17).    |
| FR-H2  | Each request states what is needed, what access is required, and **why** (§17).                                                                 |
| FR-H3  | Request kinds are distinct and visually distinguished: `credentials`, `ambiguity`, `missing-info`, `approval`, `confirmation` (§18).             |
| FR-H4  | Technical **errors**, human **decisions**, and **insufficient evidence** are presented as three different states and must not be conflated (§61). |
| FR-H5  | Submitted credential values are discarded after use. No credential storage is implemented (§62).                                               |
| FR-H6  | All human decisions are recorded in System State and remain visible in the audit log (§26).                                                    |
| FR-H7  | Resolution resumes the paused workflow from its exact point of suspension.                                                                     |

### 5.7 Assessment and feasibility --- `FR-A`

| ID     | Requirement                                                                                                                                  |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| FR-A1  | Three methodologies are assessed: Ticket Anomaly Detection, License Optimization, Application Portfolio Rationalization (§43).                  |
| FR-A2  | Each methodology declares its required evidence. Feasibility is **computed** by matching those requirements against discovered data sources and their field completeness. |
| FR-A3  | Feasibility is graded (`HIGH` / `MEDIUM` / `PARTIAL` / `LOW`), never binary.                                                                    |
| FR-A4  | Each assessment exposes: feasibility, data sufficiency, coverage, per-requirement evidence status, known limitations, and a recommendation (§21). |
| FR-A5  | License Optimization reports `PARTIAL` feasibility due to incomplete cost information, stated as a limitation on an **approvable** solution rather than a blocker (§20). |
| FR-A6  | Where feasibility is reduced, the system states what would improve it (§20).                                                                   |
| FR-A7  | Solutions are presented as cards showing feasibility, data sufficiency, evidence coverage and a description, with Review and Approve actions (§24). |
| FR-A8  | Review opens a detail surface within the workspace --- drawer or panel --- without navigating away (§25).                                       |
| FR-A9  | The detail surface shows why the methodology is feasible, the methodology's process chain, and its limitations (§25).                           |
| FR-A10 | Feasibility figures are presented as simulated demo values and must not be implied to be real enterprise measurements (§21).                    |
| FR-A11 | Feasibility is displayed as **Potential**, with the meanings of D-12: HIGH is strong value; MEDIUM is value with stated limits; PARTIAL needs deeper modelling; LOW is not yet modellable. The grade values and the rule that computes them are unchanged (FR-A2, FR-A3). |
| FR-A12 | An assessment carries a **routing-problem** flag, separate from its grade, when evidence the methodology requires exists in the environment but cannot reach the analysis: refused by policy, unreachable, or waiting on input (D-12). |
| FR-A13 | The routing-problem flag is computed from facts in System State and never authored. Changing those facts changes the flag, as FR-A2 requires of the grade. |

### 5.8 Approval --- `FR-AP`

| ID      | Requirement                                                                                          |
| ------- | ------------------------------------------------------------------------------------------------------ |
| FR-AP1  | No solution advances to implementation without explicit human approval (§26).                          |
| FR-AP2  | Solution states: `PROPOSED` → `AWAITING_APPROVAL` → `APPROVED` → `BUILDING` → `READY` → `RUNNING`, with `REJECTED` as a terminal branch (§26). |
| FR-AP3  | Approvals and rejections are recorded in System State with their outcome preserved.                    |
| FR-AP4  | All three solutions are approvable and reach a runnable state.                                        |

### 5.9 Implementation phase --- `FR-I`

| ID     | Requirement                                                                                                                  |
| ------ | ------------------------------------------------------------------------------------------------------------------------------ |
| FR-I1  | The workspace persists into implementation; the visualization pane changes from environment graph to build pipeline (§27).      |
| FR-I2  | Pipeline nodes progress through `PENDING` → `BUILDING` → `TESTING` → `VALIDATED` → `COMPLETE` (§52).                            |
| FR-I3  | The activity stream reports build progress in realistic terms (§28).                                                          |
| FR-I4  | The test stage expands into a detailed result view: named test cases, pass/fail status, and timings.                           |
| FR-I5  | No generated source code is displayed, because none is generated.                                                             |
| FR-I6  | ~~On completion, each solution is listed as Ready with a Run action (§30, §53).~~ **Superseded by FR-C6** (A-6). |

### 5.10 Analytics --- `FR-AN`

| ID      | Requirement                                                                                                                                       |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| FR-AN1  | Analytical datasets are produced by committed generators with a fixed RNG seed, built into memory at backend startup.                                |
| FR-AN2  | Datasets contain deliberately planted patterns --- a normal population plus intentionally anomalous clusters (§45).                                  |
| FR-AN3  | Anomaly labels, scores and baselines are produced at generation time. No statistics or machine learning run at request time.                          |
| FR-AN4  | ~~Headline metrics report the dataset's true counts.~~ **Superseded by FR-AN10** (A-9). |
| FR-AN5  | All aggregation is performed in the backend from record-level data. The frontend contains no analytical logic.                                       |
| FR-AN6  | Ticket Anomaly Detection receives a deep, fully polished dashboard (§44).                                                                            |
| FR-AN7  | License Optimization and Application Portfolio Rationalization each receive a dashboard with roughly 3--4 interactive charts and one drill-down path.  |
| FR-AN8  | Every chart is interactive. Decorative charts are not acceptable (§32).                                                                             |
| FR-AN9  | Supported interactions include hover tooltips, click selection, cross-filtering, time-range filtering, category filtering, drill-down, breadcrumb navigation, table views and detail panels (§32). |
| FR-AN10 | Headline metrics report the true counts of the data collected so far (FR-LF4). When collection has finished, those are the dataset's full counts (D-17). |

### 5.11 Drill-down, cross-filtering and evidence --- `FR-EV`

| ID      | Requirement                                                                                                                                             |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FR-EV1  | A single filter context --- time range, dimension selections, optional entity --- drives every chart on a dashboard simultaneously.                         |
| FR-EV2  | Any click combination filters correctly. Interaction paths are not enumerated in advance (§34).                                                            |
| FR-EV3  | Drill-down hierarchies are **declared as data per methodology** and served from the backend. Drill-down must not be implemented as hardcoded UI navigation (§56). |
| FR-EV4  | Adding a new methodology requires a generator and a hierarchy descriptor, and no new UI code (§78).                                                        |
| FR-EV5  | A breadcrumb reflects the current drill path, and the user can navigate backward through it (§55).                                                         |
| FR-EV6  | Drill-down terminates at individual underlying records (§33).                                                                                            |
| FR-EV7  | An evidence panel explains any finding with: observed value, baseline, deviation, comparable population size, contributing records, methodology reference, and validation steps (§35, §57). |
| FR-EV8  | Every figure in the evidence panel is computed from the generated records, not authored.                                                                  |

### 5.12 Operator controls --- `FR-O`

| ID     | Requirement                                                                                                                       |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| FR-O1  | Speed control (1x / 2x / instant), skip-to-next-phase, and Reset are available.                                                     |
| FR-O2  | These controls are reachable only by keyboard shortcut or a hidden panel. No transport bar is visible to the audience.              |
| FR-O3  | Speed changes apply to all subsequent simulated delays without disturbing event ordering or state.                                  |
| FR-O4  | Reset returns the system to the seed screen with all state cleared, without restarting the backend.                                 |

### 5.13 Display vocabulary --- `FR-N`

Added by the Seeding and Life rework (D-11).

| ID     | Requirement |
| ------ | ----------- |
| FR-N1  | The interface displays *solution* as **Agent Component**, the product name as **Seed** (with the version label **v0.1** beside it in the top bar and the page title, D-22), the `RUNTIME` phase as **Life**, the `INIT` phase as **Planting**, and *feasibility* as **Potential**. |
| FR-N6  | What grows out of the Seed is displayed as **Agent One VW**. The Life pane is headed "Agent One VW (ValueWise™)", the Implementation stage builds Agent One VW, and closing the seeding phase hands over to it. Each Agent Component is shown as a part of Agent One VW (D-11). |
| FR-N7  | Methodologies keep the name *methodology*. The seed analogy names the lifecycle, not the analysis (D-11). |
| FR-N2  | Renames are display-only. Identifiers, types, enum values, payload keys, API paths, event types and request ids keep their names. The glossary between the two vocabularies is D-11. |
| FR-N3  | Backend event messages are display copy, because the activity stream renders them. They follow the display vocabulary. |
| FR-N4  | "Systems" as the count of client systems in the discovery summary is not the product name, and is not renamed. |
| FR-N5  | Before Discovery begins, the Planting stage shows the systems the Adaptation layer declares, each marked as declared and not yet verified (D-13). The same declared inventory is Discovery's starting point, from one source. |

### 5.14 Seeding and Life panes --- `FR-W`

Added by the Seeding and Life rework (D-14).

| ID     | Requirement |
| ------ | ----------- |
| FR-W1  | The workspace has two panes. **Seeding** holds the Planting, Discovery, Assessment and Implementation stages, the Activity and Protection rail, and the human-input surface. **Life** holds the running system. |
| FR-W2  | A control in the top bar selects Both, Seeding only, or Life only. |
| FR-W3  | The lifecycle sets the default layout: ~~Seeding only until `IMPLEMENTATION_COMPLETE`~~ ~~Life only from planting until `IMPLEMENTATION_COMPLETE` (A-11)~~ Both from planting until seeding closes (A-13), then Life only. A manual choice holds until the next lifecycle-driven change. |
| FR-W4  | Until Implementation completes, the Life pane shows ~~a deliberate empty state~~ the growing tree (FR-G1) rather than blank space. When it completes, the tree hands over to a completion statement and Agent One VW (A-12). The grown tree stays one click away, behind a Growth control in the pane's header (A-14). |
| FR-W5  | A pending human request makes the Seeding pane visible, whatever the layout. |
| FR-W6  | Running a solution opens its dashboard inside the Life pane, not over the whole screen. A rehearsal link (D-3) opens it the same way, in the Life-only layout. |
| FR-W7  | The seed upload screen stays full-screen until the seed is planted (FR-S2). After planting, the Planting stage is the first stage of the Seeding pane. |
| FR-W8  | The reorganisation removes no existing function. Every exit criterion from M3 to M10 still holds. |

### 5.15 Growth tree --- `FR-G`

Added by the Seeding and Life rework (D-15).

| ID     | Requirement |
| ------ | ----------- |
| FR-G1  | ~~In the Seeding pane, a growth tree replaces the lifecycle strip as the progress indicator.~~ While seeding runs, a growth tree stands in the Life pane and grows vertically with the process: seed at Planting, sapling at Discovery, small plant at Assessment, tree with branches and leaves at Implementation. It names its current stage and phase. The lifecycle strip remains the Seeding pane's phase indicator (A-10, D-18). |
| FR-G2  | The tree grows one segment per completed lifecycle step, driven by events (FR-E1). |
| FR-G3  | Each capability request the protection engine evaluates triggers one watering step. A denied request waters nothing. An allowed one is seen live as a brief pulse, a blue tint through the soil and roots while the tree glows and grows a little (D-19). *Clarified by A-16:* an escalated request waters as an allowed one does, because it was not refused. A page load replays the log and may show one pulse as it does; the tree it draws is unaffected (FR-G5). |
| FR-G4  | No part of the tree claims a gen-AI or model call, because none occurs (NFR-D1). Watering is attributed to tool requests. |
| FR-G5  | The tree's state is a function of the event log. Replaying the log reproduces it exactly (FR-E7), and two runs from Reset end with the same tree (NFR-D4). |
| FR-G6  | The tree is hand-built SVG (NFR-L3). |

### 5.16 Closing the seeding phase --- `FR-C`

Added by the Seeding and Life rework (D-16).

| ID     | Requirement |
| ------ | ----------- |
| FR-C1  | After Implementation completes, a person closes the seeding phase with a single action, labelled "Run --- clean up and close seeding". |
| FR-C2  | The action is raised as a `confirmation` human request (FR-H3) that states what will happen and why (FR-H2). |
| FR-C3  | Closing performs ~~three~~ four operations (A-15), each reported in the activity stream: it consolidates the seeding phase's working notes into one record, clears the system's own scratch space, promotes each built solution's interface from its build version to its release version, and retires the tools that built Agent One VW, revoking their grants. The stream then reports the seed consumed (D-20). |
| FR-C4  | Each operation is a capability request evaluated by the protection engine (FR-P2), under rules documented in `protection.md` (FR-P7). |
| FR-C5  | All ~~three~~ four operations are simulated (A-15). None touches a seed file, a source system, the local filesystem or the network (§4.1, FR-S6, NFR-D2). |
| FR-C6  | When closing completes, the layout moves to Life only, and each ready solution is listed there with a Run action (supersedes FR-I6, A-6). |
| FR-C7  | Operator skip (FR-O1) passes through the closing step. |

### 5.17 Life pane --- `FR-LF`

Added by the Seeding and Life rework (D-14, D-17).

| ID     | Requirement |
| ------ | ----------- |
| FR-LF1 | The Life pane shows the running system: the ready solutions and their dashboards (FR-C6, FR-W6). |
| FR-LF2 | The Life pane's content is independent of the Seeding pane's. Hiding either pane changes neither pane's state (NFR-A7). |
| FR-LF3 | ~~Further Life behaviour, meaning live data collection and self-improvement, is **pending** the choice among the options in `project-notes.md` §84 (OQ-12).~~ **Resolved by D-17**, and specified as FR-LF4 to FR-LF11. |
| FR-LF4 | After the seeding phase closes, a deterministic clock advances a **collection cursor** through the final stretch of each dataset, one fixed step (a simulated week) at a time. Each step is an event naming the source, the record count and the period, labelled as simulated collection. |
| FR-LF5 | Collection reveals records the generators have already produced (FR-AN1). No record is generated at request time. |
| FR-LF6 | At fixed intervals, a **recalibration** event recomputes the baselines over the collected window and re-scores the findings. It reports what moved: the baseline from and to, and the clusters newly confirmed or withdrawn. Baselines and scores for every step are precomputed by the generators (FR-AN3). |
| FR-LF7 | The collection step is a term in the filter context (FR-EV1). Every dashboard follows it without per-dashboard code (FR-EV4), and it is URL-synced (D-3). |
| FR-LF8 | A dashboard at the top of its hierarchy follows collection. A dashboard the viewer has drilled into stays **pinned** to the step at which they drilled in. It shows how many collections are newer, and it catches up when the viewer returns to the top or asks it to. No finding changes while a viewer is inside it. |
| FR-LF9 | The evidence panel (FR-EV7) names the calibration a finding was scored under. |
| FR-LF10 | Collection is finite. It ends at the end of the dataset, reported as caught up. Operator speed applies to the clock (FR-O3), operator skip completes collection, and Reset clears it. |
| FR-LF11 | The collection and recalibration sequence is fixed. Two runs from Reset produce the same collection and recalibration events (NFR-D4, A-2). |

---

## 6. Non-functional requirements

### 6.1 Determinism and independence --- `NFR-D`

| ID      | Requirement                                                                                                     |
| ------- | ----------------------------------------------------------------------------------------------------------------- |
| NFR-D1  | No LLM, inference, or model API call occurs anywhere in the system.                                              |
| NFR-D2  | The system runs fully offline with no outbound network dependency.                                               |
| NFR-D3  | No API keys or secrets are required to run the demo.                                                             |
| NFR-D4  | Two runs from Reset produce identical event sequences, identical analytical results, and identical displayed figures, compared **modulo timestamps and durations**: the same events, in the same order, with the same types, categories, severities, payloads and figures (amended by A-2, `decisions.md`). |
| NFR-D5  | Randomness is permitted only through fixed, committed seeds.                                                     |

### 6.2 Performance --- `NFR-P`

| ID      | Requirement                                                                                     |
| ------- | ------------------------------------------------------------------------------------------------- |
| NFR-P1  | Backend startup, including dataset generation, completes in under 2 seconds **on a warm interpreter**. First-ever import of Python dependencies on a cold machine is excluded (amended by A-1, `decisions.md`). |
| NFR-P2  | Any dashboard filter or drill-down interaction returns in under 200 ms.                          |
| NFR-P3  | The activity stream remains responsive for the full duration of a demo run.                      |
| NFR-P4  | The full demo narrative runs in a presentable duration at 1x speed, and much faster at instant.   |
| NFR-P5  | Simulated delays create the perception of an active system without making the demo tedious (§46). |

### 6.3 Architecture --- `NFR-A`

| ID      | Requirement                                                                                                                              |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| NFR-A1  | The API layer depends on an event-source abstraction, never on the simulation engine directly. A real agent runtime must be substitutable behind it (§41). |
| NFR-A2  | The frontend must not require rewriting when simulated subsystems are replaced with real ones (§75).                                       |
| NFR-A3  | The workspace remains mounted across Discovery, Assessment and Implementation. Only its panes change (§13).                                |
| NFR-A4  | The real/simulated boundary of §3 is legible in the code structure (§63).                                                                  |
| NFR-A5  | No Kafka, Redis, PostgreSQL, Kubernetes, vector database, microservices, agent framework or LLM orchestration framework is introduced (§64, §79). |
| NFR-A6  | Architectural boundaries take precedence over infrastructure sophistication (§79).                                                         |
| NFR-A7  | Both panes stay mounted for the whole run. Changing the layout hides a pane and never unmounts it, which extends NFR-A3 (D-14). |

### 6.4 Visual design --- `NFR-V`

| ID      | Requirement                                                                                                                       |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| NFR-V1  | The interface is minimal, technical, premium, calm, and information-dense without clutter (§47).                                    |
| NFR-V2  | Both light and dark themes are supported and toggleable, derived from a single set of design tokens.                                |
| NFR-V3  | Chart palettes are validated for contrast in both themes.                                                                          |
| NFR-V4  | Avoided: excessive gradients, generic "AI" glow effects, robot or agent illustrations, excessive cards, fake futuristic styling, too many colours, excessive motion (§47). |
| NFR-V5  | Animation corresponds to actual state changes. Decorative animation is not acceptable (§46).                                        |
| NFR-V6  | The visual language communicates serious analytical infrastructure, not an AI toy (§47).                                           |
| NFR-V7  | Growth and watering animation respects `prefers-reduced-motion`, coalesces at instant speed rather than strobing, and stays inside NFR-V4's motion budget (D-15). |

### 6.5 Delivery --- `NFR-L`

| ID      | Requirement                                                                            |
| ------- | ---------------------------------------------------------------------------------------- |
| NFR-L1  | A single command starts backend and frontend together.                                  |
| NFR-L2  | The stack is Vue 3 + TypeScript + Pinia + Vite, FastAPI, SSE, and Apache ECharts.        |
| NFR-L3  | Bespoke visualizations --- the environment graph and build pipeline --- are hand-built SVG. |
| NFR-L4  | The demo targets a modern desktop browser at presentation resolution.                    |

---

## 7. Acceptance

V1 is complete when a presenter can, from a clean start and without
touching a terminal, perform the twenty-step narrative of §68 end to
end --- and when a sceptical viewer can then click freely through the
Ticket Anomaly dashboard, follow any anomaly down to individual source
records, and find the numbers consistent at every level.

**Amended by A-7.** The narrative now includes closing the seeding phase
(FR-C1) between Implementation and running a solution, and the dashboard
is explored in the Life pane (FR-W6). The viewer also sees Agent One VW
collect data and recalibrate at least once (FR-LF4, FR-LF6). A finding
the viewer has drilled into stays stable while collection continues, and
its evidence names the calibration it was scored under (FR-LF8, FR-LF9).

**Met at M22 (2026-10-02).** The full narrative was rehearsed at 1x
through the interface alone, with no terminal and no API call after the
page opened: 268 s of narrative against the 270 s budget, Life caught up
47 s after the hand-over, and two runs from Reset matched under A-2
(`tests/test_rehearsal.py`). See `project-notes.md` §84.5, M22.

---

## 8. Open questions

All closed. OQ-1 to OQ-7 are answered in `decisions.md` §4, OQ-8 to
OQ-12 in §7.4, and OQ-13 is deferred (§7.3). None is carried.

| ID    | Question                                                                                                        |
| ----- | ----------------------------------------------------------------------------------------------------------------- |
| OQ-1  | ~~Exact chart inventory per dashboard.~~ Ruled before M9: KPIs, treemap, bar and line charts, a focused table and the record table, with colour bound to the pattern, class or disposition. The inventory as built is in `decisions.md` §4, "As built". |
| OQ-2  | ~~Drill-down hierarchies for License Optimization and Application Portfolio Rationalization.~~ Ruled before M9. See `decisions.md` §4. |
| OQ-3  | ~~Accent colour and typeface selection.~~ Settled at M21: cobalt, and Inter with JetBrains Mono, bundled. See `decisions.md` §4. |
| OQ-4  | ~~Whether the activity stream requires virtualisation.~~ **No**, measured at M22. See `decisions.md` §4. |
| OQ-5  | ~~Whether dataset generation needs a local cache.~~ Measured: **no**. See `decisions.md` §1. |
| OQ-6  | ~~Which specific actions trigger the required `DENY` and `ESCALATE` policy decisions of FR-P6.~~ Ruled at M5. See `decisions.md` §4. |
| OQ-7  | ~~Target wall-clock duration of the full narrative at 1x.~~ Ruled: **4 to 5 minutes**. See `decisions.md` §4. |
| OQ-8  | ~~What "Agent One VW" names.~~ **What grows out of the Seed**: the framework that implements the build-and-maintain methodology. Agent Components are its parts. See `decisions.md` D-11. |
| OQ-9  | ~~Whether methodologies are renamed "Seed".~~ **No.** A seed-themed name was assessed and none was coherent. Systems is renamed Seed. See D-11. |
| OQ-10 | ~~What "routing problem" means.~~ **Evidence that exists but cannot reach the analysis.** MEDIUM and LOW wording accepted. See D-12. |
| OQ-11 | ~~Which progress bar the growth tree replaces.~~ **The lifecycle strip.** See D-15. |
| OQ-12 | ~~Which Life pane option to build.~~ **Option B, time-revealed operation.** See D-17. |
| OQ-13 | ~~Where the Agent One demo is.~~ **Deferred.** Visual continuity with Agent One is skipped for now. See `decisions.md` §7.3. |
