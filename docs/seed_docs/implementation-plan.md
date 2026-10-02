# Systems --- V1 Implementation Plan

> **Status:** Complete. Every milestone, M0 to M22, is built, one commit
> each, and the as-built state was accepted as final on 2026-10-02.
> Derived from `requirements.md`; every milestone below names the
> requirements it discharges. **Every decision in section 5 is ruled**,
> and `decisions.md` is authoritative where it differs from this
> document.
>
> **Read as a plan.** Section 2 describes the system as built, revised
> on 2026-10-02. Section 3 keeps each milestone as it was planned, with
> notes where the build went differently. The full as-built reference is
> `architecture.md`.
>
> **Amended 2026-09-23** by the Seeding and Life rework (the Alex
> Prigojine session; `decisions.md` §7). Nine milestones, M11 to M19, are
> inserted after M10. **The three milestones not yet built are
> renumbered:** Remaining dashboards moves from M11 to M20, Design pass
> from M12 to M21, and Rehearsal and hardening from M13 to M22. Their
> content is unchanged apart from notes on the rework. M0 to M10 keep
> their numbers, which the commit history uses.

---

## 1. Shape of the build

Four phases. Each ends at a state worth showing someone.

```
PHASE 1   Foundation          M0 - M2         built
PHASE 2   Narrative           M3 - M8         built
PHASE 3   Analytics           M9 - M10, M20   built
PHASE R   Seeding and Life    M11 - M19       built (stakeholder rework, decisions.md §7)
PHASE 4   Craft               M21 - M22       built
```

Phase R was not in the original plan. It relabels and reorganises what
Phases 2 and 3 built, and adds five features on top. It sits before
Phase 4 because the design pass and rehearsal must cover the interface
the rework produces, not the one it replaces.

The ordering is deliberately inverted from the temptation to start with
the dashboard. Phase 2 produces a complete, demonstrable narrative before
a single chart exists — which means if the schedule slips, it slips into
a system that still runs end to end.

---

## 2. Architecture summary

Condensed, and revised to the system as built on 2026-10-02. The
reasoning behind each choice is in `requirements.md` and
`decisions.md`. Endpoints, event types, the snapshot's fields and the
URL format are listed in `architecture.md`.

### Domain model

System State is one in-memory object (`domain/state.py`). The snapshot
the frontend fetches on connect has these top-level fields:

```
StateSnapshot
├── sequence        last event folded into this snapshot (FR-E5)
├── lifecycle       one of FR-L9's twelve states
├── phase           INIT · DISCOVERY · ASSESSMENT · IMPLEMENTATION · RUNTIME
├── blockedOn       { kind, requestId, prompt, access, reason, options }
├── humanRequests   [ { requestId, kind, prompt, status, fields, requestedAt, resolvedAt } ]
├── seed            the per-layer heading summary (FR-S5)
├── declared        the five declared systems (D-13)
├── environment     { client, nodes, edges, dataSources, summary, canvas, complete }
├── assessments     [ { name, feasibility, dataSufficiency, coverage, requirements,
│                       limitations, improvements, recommendation, routing, ... } ]
├── solutions       [ { id, name, status, methodologyId, assessmentId, dashboardId } ]
├── approvals       [ { solutionId, decision, feasibility, dataSufficiency, rule, decidedAt } ]
├── implementations [ { solutionId, components, tests, datasets, sources, status, approval } ]
├── closing         { record, scratch, promoted, retired, consumed } (D-16, D-20)
├── collection      { step, steps, every, calibration, week, caughtUp, sources } (D-17)
└── runtime         { active }
```

The event log sits beside the snapshot, not inside it. Every event
carries `sequence`, `timestamp`, `type`, `phase`, `category`, `severity`,
`message` and `payload` (FR-E3). `type` is contract and drives the
frontend's reducers; `category` and `message` are presentation and drive
the activity stream. Neither can break the other (FR-E3, FR-E4). The
protection decisions are events of type `policy.decision`, and the
protection panel is built from them.

### Lifecycle

One declared transition table, validated on every attempt; illegal
transitions raise (FR-L1, FR-L3). Blocking on human input is a
`blockedOn` flag beside the current state rather than a
`WAITING_FOR_HUMAN` state per phase (FR-L4) — this avoids a
combinatorial state table. Reset is not an edge: it rebuilds System
State from nothing (FR-L7).

### Simulation engine

Workflows are Python generators yielding **beats**. Generators give
pause/resume natively, which is exactly what FR-H7 needs. A beat is a
relative weight, never a time (D-8), with an optional floor in seconds
for the beats that must stay visible:

```python
def discovery(state: SystemState) -> Workflow:
    ...
    env.record(type="discovery.endpoint.timeout", ...)          # FR-D8
    yield Beat(weight=5, floor=3.0, label="timeout")
    ...
    submission = yield AwaitHuman(request=BlockedOn(            # FR-D7
        kind=RequestKind.CREDENTIALS,
        request_id="servicenow-incident-api", ...))
```

One asyncio task walks the registered workflows (discovery, assessment,
implementation, closing, then Life), applies their mutations to System
State and sleeps each beat for `weight × 270 s ÷ 105`, or its floor if
that is longer, divided by the speed and measured on the loop's clock
(M22). Life's beats weigh nothing and run on their floors alone (D-17). On `AwaitHuman` it parks the generator and
resumes it with `generator.send()`. Operator controls fall out of this:

| Control | Implementation                                     | Requirement  |
| ------- | -------------------------------------------------- | ------------ |
| Speed   | divide every remaining beat by 1, 2, or skip it    | FR-O1, FR-O3 |
| Skip    | drop every delay until the phase changes           | FR-O1        |
| Reset   | cancel the task, rebuild `SystemState`             | FR-O4        |

### The replaceability seam

The API layer never imports the simulation engine. It depends on the
`EventSource` protocol in `simulation/protocol.py`:

```python
class EventSource(Protocol):
    @property
    def status(self) -> RunStatus: ...
    @property
    def speed(self) -> Speed: ...
    async def start(self) -> None: ...
    async def resolve_human(self, request_id: str, submission: dict[str, Any]) -> None: ...
    def set_speed(self, speed: Speed) -> None: ...
    def skip_phase(self) -> None: ...
    async def reset(self) -> None: ...
    def snapshot(self) -> StateSnapshot: ...
```

An event source does not hand events to the API. It records them into
System State, the sole source of truth (FR-L5), and the SSE route reads
them from there through the event bus. `SimulationEngine` implements the
protocol now; a real agent runtime implements it later (NFR-A1, NFR-A2).
`runtime.py` is the one place that names the implementation. This is the
one boundary worth defending even at cost elsewhere.

### Analytics

A single **filter context** drives every chart on a dashboard:

```ts
FilterContext = {
  timeRange?: [string, string]            // accepted by the API; the UI sends months instead
  dimensions: Record<string, string[]>
  entityId?: string
  step?: number                           // Life's collection step (D-17)
}
```

Every chart click emits a delta; the breadcrumb is the ordered list of
deltas; back pops one. Cross-filtering is then automatic and no
interaction path needs anticipating (FR-EV1, FR-EV2).

```
POST /api/analytics/{solutionId}/query
{ "filter": FilterContext, "views": ["k-tickets", "volume", "clusters"] }
```

Dashboards are **data, served from the backend** (D-1). Chart
specifications carry mark type, data binding, semantic colour role,
visual weight and layout; one generic renderer draws them. Drill-down
hierarchies are data on the same principle (FR-EV3). Ticket Anomaly
Detection's, as declared in `descriptors/tickets.py`:

```python
hierarchy=[
    Level(id="all",     label="All tickets"),
    Level(id="month",   label="Month",            dimension="month"),
    Level(id="pattern", label="Pattern",          dimension="pattern"),
    Level(id="group",   label="Assignment group", dimension="group"),
    Level(id="cluster", label="Cluster",          dimension="cluster"),
    Level(id="ticket",  label="Ticket",           entity=True),
]
```

### Seeding and Life (Phase R)

The workspace splits into two panes, both mounted for the whole run
(D-14, NFR-A7). As built, while seeding runs:

```
┌──────────────────────────────────────────────────────────────────────┐
│ Seed v0.1                  [ Both | Seeding | Life ]    DISCOVERING  │
├─────────────────────────────────────────┬────────────────────────────┤
│ SEEDING                     (3/5 wide)  │ Agent One VW (ValueWise™)  │
│  lifecycle strip                        │  growth tree (D-18, D-19)  │
│  Planting · Discovery · Assessment ·    │  seed → sapling → small    │
│  Implementation stage                   │  plant → growing tree      │
│  human-input surface, when needed       │                            │
│  Activity | Protection drawer           │                            │
└─────────────────────────────────────────┴────────────────────────────┘
```

From `READY_TO_RUN` the default is Life only: Agent One VW, its live
Agent Components with Run, their dashboards, and the collection and
recalibration of D-17. The grown tree stays behind a Growth control in
the Life header (D-19).

The screen uses a display vocabulary; the code keeps its own (D-11):

| Code          | Screen          |
| ------------- | --------------- |
| the built solutions, as a whole | Agent One VW (ValueWise™) |
| solution      | Agent Component |
| methodology   | methodology (unchanged: the analogy names the lifecycle, not the analysis) |
| product name  | Seed, labelled v0.1 (D-22) |
| `RUNTIME`     | Life            |
| `INIT`        | Planting        |
| feasibility   | Potential       |
| `CLOSING_SEEDING` | Cleanup (D-20) |

### Repository structure

As built:

```
Seed V2/
├── run.py                        single-command launcher (NFR-L1)
├── run.ps1                       pip-based setup and launch, where uv is blocked (D-21)
├── pyproject.toml, uv.lock       Python project; requirements*.txt exported from the lock
├── seeds/                        core.md, adaptation.md, protection.md
├── docs/
├── backend/app/
│   ├── main.py                   FastAPI app; datasets built at startup
│   ├── config.py                 ports, keepalive, the 270 s budget and its weight
│   ├── runtime.py                the one state, bus and EventSource (NFR-A1)
│   ├── bus.py                    fan-out from the event log to SSE streams
│   ├── api/                      health, state, seed, events, operator, human,
│   │                             solutions, environment, protection, analytics
│   ├── domain/                   lifecycle, events, state, solutions,
│   │                             presentation, schema
│   ├── simulation/
│   │   ├── protocol.py           EventSource — the NFR-A1 seam
│   │   ├── engine.py             beat runner, speed, skip, reset
│   │   ├── beats.py              Beat and AwaitHuman
│   │   └── workflows/            discovery, assessment, implementation,
│   │                             closing, life, gate, registry
│   ├── knowledge/                seed_loader, methodologies, feasibility,
│   │                             routing, solutions, builds
│   ├── environment/              acme.py (five systems, coordinates), model.py
│   ├── protection/               rules, engine, capabilities
│   └── analytics/
│       ├── generator/            tickets, licenses, applications, and the shared clock
│       ├── descriptors/          one dashboard descriptor per methodology (D-1)
│       ├── schema.py             the descriptor schema
│       ├── store.py              in-memory frames, calibrations, Life's plan
│       ├── query.py              filter context → figures
│       └── evidence.py           the evidence panel's figures
├── backend/tests/                17 files, 561 tests (D-7)
└── frontend/src/
    ├── App.vue                   top bar and the two panes
    ├── stores/                   system, events, layout, operator, dashboard,
    │                             protection, seed, theme
    ├── design/                   tokens.css, base.css, presentation.ts,
    │                             growth.ts, format.ts
    ├── charts/                   EChart.vue, options.ts (D-5)
    ├── components/               stages, environment graph, build lanes,
    │                             activity, protection, human input, growth
    │                             tree, layout control, operator panel,
    │                             dashboard/ (KPI, chart, table, drill bar,
    │                             evidence panel)
    └── views/
        ├── SeedView.vue          full-screen until planted (FR-W7)
        ├── WorkspaceView.vue     the Seeding pane
        ├── LifeView.vue          the Life pane
        └── DashboardView.vue     the one generic renderer (D-1),
                                  lazily loaded inside the Life pane
```

---

## 3. Milestones

### Status

| Milestone | Tag    | Status | Commit |
| --------- | ------ | ------ | ------ |
| M0 Walking skeleton          | —      | Built | `e496edd` |
| M1 State and event backbone  | —      | Built | `76ca4bd` |
| M2 Simulation engine         | —      | Built | `94663f5` |
| M3 Seed and INIT             | —      | Built | `5f458fe` |
| M4 Workspace shell           | —      | Built | `1c9450e` |
| M5 Protection layer          | —      | Built | `20a9146` |
| M6 Discovery                 | —      | Built | `2b8dc8f` |
| M7 Assessment and approval   | —      | Built | `893da34` |
| M8 Implementation and run    | —      | Built | `dabd605` |
| M9 Analytics core            | —      | Built | `149a710` |
| M10 Ticket Anomaly dashboard | —      | Built | `08fc371` |
| M11 Display vocabulary       | RENAME | Built | `58b03cb` |
| M12 Feasibility reference audit | RENAME (audit) | Built | `9436189` |
| M13 Feasibility displayed as Potential | RENAME | Built | `1855e18` |
| M14 Seeding and Life panes   | MOVE   | Built | `34ce3d9` |
| M15 Declared stack at Planting | NEW  | Built | `64ed030` |
| M16 Routing-problem flag     | NEW    | Built | `4cf715d` |
| M17 Growth tree              | NEW    | Built | `8fa369a` |
| M18 Closing the seeding phase | NEW   | Built | `8e2c525` |
| M19 Life: collection and recalibration | NEW | Built | `889ceb7` |
| M20 Remaining dashboards *(was M11)* | — | Built | `4e8f552` |
| M21 Design pass *(was M12)*  | —      | Built | `60726f2` |
| M22 Rehearsal and hardening *(was M13)* | — | Built | `6a7be84` |

Commits between milestones, each a follow-up the build log in
`project-notes.md` §84.5 records:

| Commit | Change |
| ------ | ------ |
| `a2aa8de` | Planning documents and repository ignore rules |
| `05c0ca6` | The lifecycle phase-name ruling (`decisions.md` §4) |
| `ab8a247` | OQ-1 and OQ-2 ruled: chart inventory and hierarchies |
| `044b592` | `requirements.txt` and `requirements-dev.txt`, exported from `uv.lock` |
| `a4dad84` | The Seeding and Life rework planned (Phase R) |
| `798353b`, `6937f64` | Potential's ordered colour scale |
| `cdbf4be` | Two bugs M14's live check found in earlier milestones |
| `7bfa52f` | PR-033's refusal made the narrative's routing problem |
| `6e2c8e2` | The growth tree moves to the Life pane (D-18) |
| `4dc2f91` | The rail docks in Both; the tree fills out |
| `178b254` | Both during the build, and the Growth control (D-19) |
| `fb5145b` | The watering pulse; stem and roots joined |
| `45599ca`, `e5c3251` | Roots that grow and blur; Cleanup by name; a leaner Life pane |
| `6bb2d72` | `run.ps1`, setup and launch without uv (D-21) |
| `14fea9f` | The product displayed as Seed v0.1 (D-22) |

The rework reworks, rather than extends, three built milestones, and
each is flagged where it happens: **M4**'s single workspace becomes the
Seeding pane (M14); **M7**'s grade presentation becomes Potential (M13,
M16); and **M8**'s Implementation-to-Run transition gains the closing
step (M18). M3, M8 and M10 are also relocated or relabelled without
functional change. None of the built milestones' requirements is
dropped; four are superseded with successors (A-3 to A-6).

### Phase 1 — Foundation

---

**M0 · Walking skeleton**

Repo scaffold, `run.py` launcher on `uv` (D-10), FastAPI app, Vite +
Vue 3 + TS + Pinia, design-token file with both themes stubbed, one
trivial event travelling backend → SSE → browser. `run.py` completes its
imports before signalling readiness (A-1).

*Discharges:* NFR-L1, NFR-L2, NFR-L4
*Exit:* one command starts both services; the browser renders a live
event; the theme toggle flips tokens.
*Later (D-21):* `run.ps1` was added as a second single-command launcher
for a machine where uv is blocked. It installs with pip and hands over
to `run.py`.

---

**M1 · State and event backbone**

Domain models, lifecycle machine and transition table, `SystemState`,
event schema and factory, event log, SSE endpoint with `Last-Event-ID`
replay, `GET /api/state` snapshot, frontend event store implementing
snapshot-then-stream with sequence-gap detection.

*Discharges:* FR-L1–L5, FR-L7, FR-E1–E7
*Exit:* a throwaway workflow drives real state transitions; killing and
restoring the SSE connection replays exactly; an illegal transition
raises rather than mutating.

---

**M2 · Simulation engine**

Beat runner, generator-based workflows, `await_human` park/resume,
speed/skip/reset, `EventSource` protocol and its simulation
implementation. Beats carry **relative weights** scaled to a configured
total duration (D-8), set to 270 s for the 4--5 minute target (OQ-7).

*Discharges:* FR-O1, FR-O3, FR-O4, FR-H7, NFR-A1
*Exit:* a two-step workflow pauses for input, resumes on submission, and
survives being sped up, skipped and reset.

> **Phase 1 exit:** nothing worth showing, but every subsequent milestone
> is now additive rather than structural.

---

### Phase 2 — Narrative

---

**M3 · Seed and INIT**

Author the three seed files — real methodology, mapping and policy
content, since they are a deliverable in their own right (FR-S1). Seed
loader with Markdown heading parsing, INIT screen with the plant gesture,
plant → initialize transition, hidden sample-seed shortcut.

*Discharges:* FR-S1–S7
*Exit:* dragging in three files produces a genuine per-layer heading
summary and advances the lifecycle.
*Note:* the writing of the seed content is real work and easy to
underestimate.

---

**M4 · Workspace shell**

Persistent `WorkspaceView`, lifecycle strip, activity stream, human-input
surface, protection panel shell, overall layout.

*Discharges:* FR-L6, FR-E8, FR-E9, FR-H1–H4, NFR-A3
*Exit:* the workspace renders live events from M2's throwaway workflow
and never unmounts across phase changes.

---

**M5 · Protection layer**

Rule set authored in Python and mirrored into `protection.md`, evaluation
engine, policy events inline in the activity stream, protection panel
with live counts and a filterable audit log.

*Discharges:* FR-P1–P7
*Exit:* a requested action returns a real `ALLOW`/`DENY`/`ESCALATE`
decision citing a rule id, and it appears in both the stream and the
panel.
*Note:* sequenced before Discovery because every discovery action passes
through this gate (FR-P2).

---

**M6 · Discovery**

ACME environment definition — five systems expanded to roughly thirty
nodes — discovery workflow including the credential pause and the
timeout/retry, SVG environment graph with progressive node appearance and
status transitions, computed completion counts.

*Discharges:* FR-D1–D10, FR-H5, FR-H6
*Exit:* discovery runs start to finish, pauses once for credentials,
recovers from one timeout, and reports counts derived from the graph
rather than authored.
*Pacing (OQ-7):* discovery takes roughly half the 270 s budget. Nodes
appear in **grouped bursts per system**, not individually --- thirty
individual appearances do not fit a readable pace. The credential pause
and the timeout recovery carry fixed weights that do not scale down,
since both are meaning-bearing beats (FR-D7, FR-D8).

---

**M7 · Assessment and approval**

Methodology definitions with declared evidence requirements, feasibility
computed by matching requirements against data-source field
completeness, solution cards, review drawer, approve/reject with recorded
outcomes.

*Discharges:* FR-A1–A10, FR-AP1–AP4
*Exit:* editing a data source's field completeness visibly changes a
feasibility grade — the proof that FR-A2 is computed rather than
authored.

---

**M8 · Implementation and run**

Build workflow, SVG pipeline with node state progression, expandable
test-results detail, ready-to-run listing, run action.

*Discharges:* FR-I1–I6, FR-L8
*Exit:* an approved solution builds, tests, becomes Ready, and Run
transitions to a (still stubbed) dashboard.

> **Phase 2 exit — the significant one.** The entire §68 narrative runs
> end to end. Everything from here is about what the viewer finds when
> they arrive.

---

### Phase 3 — Analytics

---

**M9 · Analytics core** *(load-bearing)*

Three generators with fixed seeds and planted anomaly clusters, in-memory
store, query engine translating filter context to aggregates, hierarchy
descriptors, evidence endpoint, records endpoint --- **and the chart
specification schema that D-1 makes load-bearing**, covering mark type,
data binding, semantic colour role, visual weight and layout.
OQ-1 moves here from M10: under D-1 the chart inventory defines the
schema, so it must be settled before the schema is built.

*Discharges:* FR-AN1–AN5, FR-EV1–EV4, FR-EV6–EV8, NFR-D4, NFR-D5,
NFR-P1, NFR-P2
*Exit:* an arbitrary filter combination returns correct aggregates in
under 200 ms, and an evidence query returns figures computed from real
rows.
*Note:* under D-1 this is the schedule's single point of failure, not
merely its pivot. If the schema is right, M10 and M20 are both
configuration. If it is not expressive enough, no amount of M21 effort
recovers the craft --- see R-6. Design it against §54's seven Ticket
Anomaly charts, the hardest case, before writing the renderer.
*Measured:* generation costs 0.108 s and a two-key groupby 6 ms, so
NFR-P1 and NFR-P2 have ample headroom (R-3 closed, OQ-5 answered no).

---

**M10 · Ticket Anomaly dashboard**

The **generic descriptor-driven renderer** (D-1): ECharts wrappers
resolving semantic colour roles against design tokens (D-5), KPI row,
chart set, cross-filter wiring, URL-synced filter context (D-3),
drill-down and breadcrumb, evidence panel, underlying-record table. The
Ticket Anomaly dashboard is a descriptor, not a component.

*Discharges:* FR-AN6, FR-AN8, FR-AN9, FR-EV5
*Exit:* a viewer can click freely from a headline number to an individual
ticket and find every intermediate figure consistent --- and the dashboard
that achieves this contains no methodology-specific UI code.

---

### Phase R — Seeding and Life

From the Alex Prigojine session (`decisions.md` §7). Each milestone is
tagged:

- **RENAME** changes display copy only.
- **MOVE** relocates an existing component without changing what it does.
- **NEW** adds logic.

The milestones run from lowest risk to highest: renames, then the pane
move, then new features. The new features are ordered by how much of
the tested core each one touches. One rule holds across the phase:
**no existing test assertion changes until M18.** Through M15 the
unedited suite passing is the proof that nothing built was disturbed.
M16 and M17 add tests without editing any. M18 is the one milestone that
must edit an assertion, and it is ordered last among the lifecycle work
for that reason.

Every open question raised by the rework was answered before Phase R
began (OQ-8 to OQ-12), or deferred (OQ-13). No milestone in the phase
is blocked.

---

**M11 · RENAME · Display vocabulary**

The copy half of D-11, except Feasibility. Feasibility carries semantics
and load-bearing references, so it gets its own audit (M12) and its own
pass (M13).

- Product name "Systems" becomes "Seed": `SeedView.vue:45`,
  `WorkspaceView.vue:41`, and the page title in `index.html:6`.
- Phase labels: "Init" becomes "Planting" (`LifecycleStrip.vue:13`), and
  "Runtime" becomes "Life" (`LifecycleStrip.vue:17`). The INIT stage's
  heading "Seed" becomes "Planting" (`StagePane.vue:46`).
- "Solution" becomes "Agent Component" in display copy. In the frontend
  that includes `RuntimeStage.vue:66`, `ImplementationStage.vue:36,43`,
  `HumanRequest.vue:147`, `ReviewDrawer.vue:154` and the status labels.
  In the backend it covers the event messages the activity stream
  renders (FR-N3). About 57 quoted strings mention "solution" or
  "runtime" across seven backend files. Only those that reach the screen
  change.
- Agent One VW, the name for the whole (FR-N6): the Implementation
  stage's heading becomes "Building Agent One VW", and its copy calls each
  lane an Agent Component of it. The Life pane's heading lands with the
  pane in M14, and the closing hand-over lands with closing in M18.
- Headings in the seed files that contain the old words, because FR-S5
  displays headings. Prose changes are optional.
- **Not renamed:** *methodology*, anywhere (FR-N7).

**Load-bearing. Do not change:**

| Reference | Where | Why |
| --------- | ----- | --- |
| `Solution`, `SolutionStatus` types; `solutionId` | `stores/system.ts`, backend payloads | Contract (D-11) |
| `/api/solutions/*` | `api/solutions.py`, `stores/events.ts` | Contract |
| Event types `solution.*` | backend workflows; asserted in `test_presentation.py:113-129` | Contract, and tested |
| Request id `'solution-approval'` | `AssessmentStage.vue:25` and `knowledge/solutions.py:32` | Looks like copy, but it is an id matched across the boundary, so a rename breaks the approval flow silently (R-13) |
| Phase values `INIT`, `RUNTIME` | `domain/lifecycle.py`, `stores/system.ts` | Ruled in `decisions.md` §4 |
| "Systems" count label | `EnvironmentStage.vue:74` | Counts client systems. Not the product name (FR-N4) |
| Component file names | `SolutionCard.vue`, `RuntimeStage.vue` | Renaming them is churn with no visible effect |

*Discharges:* FR-N1 (all but Potential), FR-N2, FR-N3, FR-N4, FR-N6 (in
part), FR-N7
*Exit:* a full narrative run shows no "Solution", no "Systems" as the
product name, no "Init" and no "Runtime". `pytest` passes **with no test
edited**, which proves no logic moved. Typecheck and build pass. The
approval flow is exercised by hand (R-13).
*Risk:* lowest.

---

**M12 · RENAME (audit) · Feasibility references, classified**

**No code changes.** Re-verify the preliminary inventory below against
the code as it then stands. Classify every occurrence of `feasib` in
`backend/app`, `backend/tests`, `frontend/src` and `seeds/`, and mark
each load-bearing reference as either *keep* or *change with the
contract*. Replace the preliminary inventory with the verified one here,
and have it reviewed before M13 begins. A reference that is both display
and load-bearing counts as load-bearing.

*Verified inventory, taken 2026-09-23 against the code at `58b03cb`
(after M11). It replaces the preliminary inventory taken while
planning.*

`feasib` occurs on 65 lines: 31 in `backend/app`, 12 in `backend/tests`,
19 in `frontend/src` and 3 in `seeds/`. The tables below also cover the
grade references that do not contain the word but carry the same risk:
the `Grade` values, `grade_of`, `RECOMMENDATIONS`, the improvement
grades and the grade selectors. Every line is in exactly one table.

**Differences from the preliminary inventory.**

- One more contract consumer: the `Approval` type's `feasibility` field
  (`stores/system.ts:235`).
- A new class, **tested**. `test_assessment.py:201` asserts the regrade
  text "License Optimization PARTIAL to HIGH", which
  `knowledge/solutions.py:178` builds. The preliminary claim that no
  test asserts on feasibility display text holds for the word itself. It
  does not hold for this format.
- One more display string: the deployment request's purpose,
  "…the assessment found feasible" (`workflows/assessment.py:138`). The
  protection panel shows it, and no rule reads it (`protection/rules.py:16-20`).
- The `recommendation` key, which the preliminary inventory left out, is
  contract. A test asserts that its value is non-empty.
- The `Grade` type is at `stores/system.ts:161`, not `:162`.
- `ReviewDrawer.vue` had grade selectors for HIGH, PARTIAL and LOW only,
  and MEDIUM took the plain text colour on both surfaces. *Updated after
  M14:* the follow-up that gave Potential its own colour scale added the
  missing MEDIUM rule. Every grade surface now reads the `--grade-*`
  tokens: green, olive, amber, grey (`project-notes.md` §84.5).

**Load-bearing: contract.** Payload keys shared by the backend and the
frontend. All are kept, per D-11.

| Reference | Produced | Consumed |
| --------- | -------- | -------- |
| `feasibility` on each assessment | `knowledge/feasibility.py:142` | `stores/system.ts:197`; `SolutionCard.vue:40`, `ReviewDrawer.vue:70`, `RuntimeStage.vue:30`; read by `workflows/assessment.py:83,114` and `knowledge/solutions.py:140,177-178`; asserted in `test_assessment.py:66,133,219,388` |
| `feasibility` on each approval record | `knowledge/solutions.py:133` | `stores/system.ts:235`; `ReviewDrawer.vue:167`; asserted in `test_assessment.py:231` |
| `appearsFeasible` in the discovery summary | `environment/model.py:453` | `stores/system.ts:136`; `EnvironmentStage.vue:116,123`; counted at `workflows/discovery.py:467`; asserted in `test_discovery.py:332,344` |
| `from` and `to` grades on improvements | `knowledge/feasibility.py:206-207` | `stores/system.ts:187-188`; `ReviewDrawer.vue:128-129` |
| `recommendation` on each assessment | `knowledge/feasibility.py:149` | `ReviewDrawer.vue:137`; asserted non-empty in `test_assessment.py:138` |

**Load-bearing: logic.** Kept.

| Reference | Where | Note |
| --------- | ----- | ---- |
| Module name `knowledge/feasibility.py` | imported at `knowledge/builds.py:37`, `knowledge/solutions.py:29`, `workflows/assessment.py:34`, `test_assessment.py:25` | Keep. Renaming the module is churn with no visible effect |
| `Grade` values HIGH, MEDIUM, PARTIAL, LOW | `feasibility.py:52-56`; `stores/system.ts:161` | Keep. D-12 changes their meaning on screen, not their values |
| `grade_of` thresholds | `feasibility.py:84-93` | Keep. The computation is unchanged (FR-A11) |
| `RECOMMENDATIONS` | `feasibility.py:59-66` | **Keys** are logic and stay. **Values** are display copy, and M13 rewrites them |
| Regrade comparison | `knowledge/solutions.py:177` | Keep |
| Grade list in the assessment summary | `workflows/assessment.py:114` | Keep. It reads the key, and the message it builds shows the grades without the word |
| Local count `feasible` | `workflows/discovery.py:467` | Keep. A local variable. The message it feeds (`:474`) is already neutral |
| Grade segment fill | `SolutionCard.vue:28,60` | Keep |

**Load-bearing: tested.** An edit here fails the unedited suite.

| Reference | Where | Test |
| --------- | ----- | ---- |
| Regrade text `"{name} {from} to {to}"` | `knowledge/solutions.py:178` | `test_assessment.py:201`. Keep the format. Only the prefix at `:188` is display |
| A recommendation exists for every grade | `feasibility.py:59-66` values | `test_assessment.py:138`. The rewritten values must stay non-empty |

**Load-bearing: silent failure.** Breaking these produces no type error
and fails no test (R-13).

| Reference | Where |
| --------- | ----- |
| CSS selectors on grade values, `[data-grade='…']` | `SolutionCard.vue:201-215`, `ReviewDrawer.vue:259-273` and, since the post-M14 colour follow-up, `RuntimeStage.vue:208-222`; all four grades on each, coloured by the `--grade-*` tokens in `design/tokens.css` |
| `data-feasible` attribute and its selector | `EnvironmentStage.vue:116,332` |

**Display only. M13 changes these.** The wording below was reviewed and
agreed on 2026-09-23. Only the recommendation texts are rewritten in
substance, and M13 still reviews them as content.

| Where | Now | Proposed |
| ----- | --- | -------- |
| `SolutionCard.vue:53` | Feasibility | Potential |
| `ReviewDrawer.vue:69` | Feasibility | Potential |
| `ReviewDrawer.vue:85` | Why this is feasible | Why the value is within reach |
| `ReviewDrawer.vue:166` | …on feasibility {grade}… | …on potential {grade}… |
| `RuntimeStage.vue:85` | Feasibility {grade} | Potential {grade} |
| `AssessmentStage.vue:100` | Feasibility is computed from field completeness… | Potential is computed from field completeness… |
| `EnvironmentStage.vue:123` | Appears feasible | Evidence located |
| `EnvironmentStage.vue:127` | Feasibility is graded in assessment, against field completeness. | Potential is graded in assessment, against field completeness. |
| `workflows/assessment.py:83` | {name}: feasibility {grade}. | {name}: potential {grade}. |
| `workflows/assessment.py:138` | …the Agent Components the assessment found feasible. | …the Agent Components the assessment proposed. |
| `knowledge/solutions.py:142` | …approved for implementation, on feasibility {grade}. | …on potential {grade}. |
| `knowledge/solutions.py:146` | …rejected, on feasibility {grade}. | …on potential {grade}. |
| `knowledge/solutions.py:188` | Feasibility moved: | Potential moved: |
| `knowledge/solutions.py:190` | No feasibility grade changed. | No potential grade changed. |
| `feasibility.py:60` HIGH | Proceed. | Strong value. Proceed: the Agent Component can deliver its full findings. |
| `feasibility.py:61-62` MEDIUM | Proceed. The limitations are stated with the evidence and do not prevent a conclusion. | Value, with stated limits. Proceed: the findings hold, and the limits are named beside them. |
| `feasibility.py:63-64` PARTIAL | Proceed with reduced scope. Conclusions that rest on incomplete evidence are reported as insufficient until it improves. | Needs deeper modelling. Proceed with reduced scope: findings that rest on incomplete evidence are withheld until the data improves or the model is extended. |
| `feasibility.py:65` LOW | Do not proceed until the missing evidence is supplied. | Not yet modellable. Evidence the methodology needs is missing. Do not proceed until it is supplied. |
| `seeds/adaptation.md:218` | `## Feasibility` | `## Potential`. The heading count FR-S5 displays is unchanged |
| `seeds/adaptation.md:220-222` | Adaptation reports what each Core methodology can be run on… Feasibility is a statement about evidence coverage… | Adaptation reports how much of each Core methodology's value is within reach in this environment. Potential is a statement about evidence coverage… |
| `seeds/adaptation.md:224` | Column "Feasible" | Column "Potential". See finding 1 |

**Comments and docstrings.** These have no function. Update them only
where they explain display behaviour. M13 updates one of them:
`ReviewDrawer.vue:21`, which names the section title ("why this is
feasible"). It keeps the rest, which describe the computation, and the
computation is still feasibility in the code vocabulary (R-12):
`api/environment.py:5`, `domain/solutions.py:3`,
`environment/model.py:94,314,413`, `feasibility.py:1,17,23,180`,
`methodologies.py:12`, `seed_loader.py:9`, `knowledge/solutions.py:12`,
`workflows/assessment.py:4`, `OperatorPanel.vue:46`.

**Tests.** The other test lines are names and docstrings:
`test_assessment.py:4,88,123` and `test_discovery.py:335`. They are
kept, because no test is edited before M18.

**Findings, agreed 2026-09-23.** These are not classifications, but
the audit surfaced them. Both proposals were accepted.

1. **The seed's table disagrees with the computed grades.** In
   `adaptation.md:224-228`, License Optimization is "Yes" and
   Application Portfolio Rationalization is "Partially". The computation
   grades them PARTIAL (unit price 64% complete) and MEDIUM. The limiting
   factors named in the table are also not the ones the computation
   finds. FR-S6 means the table drives nothing, but it is the document a
   sceptical viewer opens (FR-S1). Proposal for M13: the Potential
   column shows the computed grades, HIGH, PARTIAL and MEDIUM, and the
   limiting factors match what assessment reports.
2. **The deployment purpose** is not in the preliminary inventory. The
   wording proposed above drops the claim rather than rephrasing it,
   because "found potential in" reads badly.

No test asserts on the word "feasibility" in any display text. The one
display-adjacent assertion is the regrade format above, and the proposed
changes keep it. M13 can therefore be verified by the unedited suite.

*Discharges:* nothing directly. It gates M13 (R-13).
*Exit:* every occurrence is classified, and the list of what M13 will
change has been reviewed and agreed.
*Risk:* none in itself. It exists to lower M13's.

---

**M13 · RENAME · Feasibility displayed as Potential**

Change only what M12 classified as display:

- labels and section titles ("Feasibility" becomes "Potential"; "Why this
  is feasible" is reworded to the value framing)
- the discovery summary's verdict ("Appears feasible" becomes "Evidence
  located")
- backend event messages
- the recommendation texts, rewritten to D-12's meanings
- the `## Feasibility` section of `adaptation.md`

Keeps: the `feasibility` and `appearsFeasible` keys, the `Grade` values,
`grade_of`, the CSS value selectors and the module name.

*Reworks:* M7's presentation of the grade, with no change to its
computation.
*Discharges:* FR-A11, FR-N1 (Potential)
*Exit:* a full run shows no "feasib…" anywhere on screen. `pytest` passes
with no test edited. All four grade colours render correctly in both
themes, which is the silent-failure check (R-13).
*Risk:* low. The recommendation texts carry meaning, so they are
reviewed as content, not just proofread.

---

**M14 · MOVE · Seeding and Life panes**

D-14, as a relocation:

- A top bar with the identity and the layout control (Both, Seeding,
  Life).
- **Seeding pane:** today's `WorkspaceView` body (`StagePane` for INIT to
  IMPLEMENTATION, the rail, `HumanRequest`), unchanged in content.
  `LifecycleStrip` stays in this pane until M17 replaces it.
- **Life pane:** headed "Agent One VW (ValueWise™)" (FR-N6).
  `RuntimeStage` is moved out of `StagePane`, and `DashboardView` is
  moved from `App.vue`'s full-screen overlay into the pane, still lazily
  loaded.
- Default layout driven by the lifecycle, with manual override (FR-W3).
- Life's empty state (FR-W4). *Replaced by the growing tree at D-18;
  the Life pane is never empty as built.*
- A pending human request forces the Seeding pane visible (FR-W5).
- Rehearsal links open into Life (FR-W6).
- `SeedView` stays full-screen until planted (FR-W7).

Until M18 lands, the lifecycle still passes directly from
`IMPLEMENTATION_COMPLETE` to `READY_TO_RUN`, and the Life pane fills at
that point. **M14 must leave the narrative runnable end to end without
M18.**

*Reworks:* M4's single workspace, which becomes the Seeding pane; the
placement of M8's ready list; and M10's full-screen dashboard.
*Discharges:* FR-W1–W8, FR-LF1, FR-LF2, FR-L10, NFR-A7
*Exit:* the full narrative runs in the new shell, with all three layouts
reachable. Running a component opens its dashboard inside Life.
Returning keeps the activity stream's scroll position and the
dashboard's URL filter state. **Every M3 to M10 exit criterion is
re-verified** (FR-W8).
*Risk:* medium. The move touches `App.vue`'s screen selection and the
dashboard's mount point. URL sync (D-3) and the async dashboard load are
the likeliest things to break.

---

**M15 · NEW · Declared stack at Planting**

D-13. The Adaptation layer's declared inventory enters System State at
`INITIALIZED` as an additive snapshot field, taken from `acme.py`'s
`SYSTEM_ORDER`, the same source Discovery's first beat reads. The
Planting stage lists it, with each system marked declared and not yet
verified. Once Discovery reaches a system, its status follows the
environment graph.

*Discharges:* FR-N5
*Exit:* after planting and before Discovery, the five declared systems
appear, marked unverified. Discovery's first beat names the same five,
from the same source.
*Risk:* low. The field is additive, and no existing assertion changes.

---

**M16 · NEW · Routing-problem flag**

D-12. The meaning was confirmed at OQ-10: evidence that exists but
cannot reach the analysis.

The flag is computed per assessment from System State: it is raised for
any required concept whose carrying source was denied by policy, is in
error status, or is blocked on input. It is an additive field on the
assessment. The card and the review drawer show it apart from the grade,
in its own treatment and never the fault colour, which keeps FR-H4's
distinctions.

The assessment suite gains tests in M7's style: change the fact, and the
flag moves. Establish whether any methodology carries the flag in the
scripted run; PR-033 is the candidate. If none does, record that and
raise it (D-12).

*Reworks:* M7's assessment payload, additively.
*Discharges:* FR-A12, FR-A13
*Exit:* the flag is computed, tested and shown separately from the
grade. Changing a node's status or a policy decision changes it.
*Risk:* medium. A new contract field, and a new state for the viewer to
read correctly.

---

**M17 · NEW · Growth tree**

D-15. OQ-11 confirmed that the tree replaces the lifecycle strip.

A hand-built SVG tree in the Seeding pane replaces `LifecycleStrip`
there, and carries the phase labels (FR-G1). Segments grow from
lifecycle events. Watering comes from protection decisions, and a denied
request waters nothing. It honours reduced motion and coalesces at
instant speed (NFR-V7). **Measure the number of policy decisions per run
before designing the watering step.** If it runs to hundreds, steps are
batched.

*Supersedes:* FR-L6, by A-4
*Reworked by D-18 (2026-09-24), after review:* the tree moved to the Life
pane and grows vertically from seed to tree while seeding runs, then hands
over to Agent One VW when the build completes. The lifecycle strip
returned to the Seeding pane (A-10), and the default layout during the
build is Life only (A-11, A-12).
*Reworked again by D-19:* the default during the build is Both (A-13),
and the grown tree stays behind a Growth control after the hand-over
(A-14).
*Discharges:* FR-G1–G6, NFR-V7
*Exit:* a tree rebuilt from a snapshot plus replay is identical to one
grown live. Two runs from Reset end with the same tree. Nothing strobes
at instant speed. Reduced motion shows the same states without
animation.
*Risk:* medium. The technical risk is low, and the design risk is high
(R-14).

---

**M18 · NEW · Closing the seeding phase**

D-16.

**Backend.** The `CLOSING_SEEDING` state and its edges. A closing
workflow: a `confirmation` request, then three simulated operations,
each policy-evaluated. The new rules go into the rule set **and**
`protection.md`, under the D-6 parity test. Closing gets a D-8 weight of
roughly 10 to 15 seconds.

**Frontend.** The action at the end of the Implementation stage. On
completion the layout moves to Life only, and the stream records the
hand-over to Agent One VW (FR-N6). The ready list appears in Life
(FR-C6).

Operator skip passes through closing (FR-C7). The narrative test harness
(`tests/narrative.py`) resolves the new confirmation.

*Reworks:* M8's transition from Implementation to Run.
*Also (D-20):* a fourth operation retires the build tools (PR-095), the
stream reports the seed consumed, and the tree sheds its stake and seed
husk as closing proceeds.
*Also (D-18):* move the Life pane's hand-over from the growing tree to Agent
One VW, which M17 triggers at `IMPLEMENTATION_COMPLETE`, to the end of
closing, and keep the tree up through `CLOSING_SEEDING`.
*Supersedes:* FR-L2 by A-3, and FR-I6 by A-6
*Discharges:* FR-L9, FR-C1–C7
*Exit:* the narrative pauses once more, for confirmation. The three
operations appear in the stream with their policy decisions and rule
ids, and the protection panel counts them. The layout hands over to
Life. The state-machine suite covers the new edges, both legal and
illegal, and the parity test passes.
*Note:* this is the only milestone in Phase R that must **edit** an
existing assertion. The state-machine suite currently holds the edge
`IMPLEMENTATION_COMPLETE → READY_TO_RUN` legal, and it no longer is.
Together with the rule-set change, that is why this milestone comes last
among the lifecycle work.
*Risk:* high.

---

**M19 · NEW · Life: collection and recalibration**

D-17, Option B from `project-notes.md` §84.3.

**Generators.** Each generator (tickets, licences, applications) also
precomputes, for every collection step, that step's baselines, scores
and finding membership. The single-step computation that exists today
runs once per step at startup. **Measure first:** generation costs
0.108 s now, so N steps should stay far inside NFR-P1, but confirm this
rather than assume it.

**Query engine.** The collection step becomes one more term in the
filter context. Aggregates count only records collected up to that step,
and findings are read from that step's precomputed scores. It is
URL-synced with the rest of the filter context (D-3).

**Life workflow.** A beat workflow starts when closing completes (M18).
Each beat advances the system cursor one step and emits a collection
event. Every few steps it emits a recalibration event that reports what
moved. It ends caught up. Operator speed, skip and Reset apply
(FR-LF10).

**Frontend.** The Life pane shows collection progress under the Agent
One VW heading. A dashboard at the top of its hierarchy follows the
system cursor. A drilled-in dashboard pins to its step, shows how many
collections are newer, and catches up on return to the top or on
request (FR-LF8). The evidence panel names the calibration (FR-LF9).

**Starting values, tuned at M22:** reveal the final 8 to 12 simulated
weeks, one week per step, a few seconds apart at 1x, and recalibrate
every 4 steps. That lets Agent One VW catch up in under a minute of
presenter time. Collection happens after the 270-second narrative, so
it does not draw on that budget.
*As built, and kept at M22:* twelve weeks, ISO weeks 24 to 35 of 2026,
3 s a step at 1x and 2 s more per recalibration, three
recalibrations. Life caught up 47 s after the hand-over in the 1x
rehearsal (D-17, "As built").

*Supersedes:* FR-AN4, by A-9. *Clarifies:* the Evolution exclusion in
§4.1, by A-8.
*Discharges:* FR-LF4–LF11, FR-AN10
*Exit:*
- After closing, the stream shows collection steps and at least one
  recalibration that reports a baseline moving and clusters confirmed
  or withdrawn.
- KPIs grow step by step, and at the caught-up state they equal the full
  dataset's counts.
- A drilled-in finding does not change while collection continues, and
  it catches up on request.
- A rehearsal URL opens a chosen step.
- Two runs from Reset produce the same collection and recalibration
  events.
- The query-engine suite covers the step term against record-level
  ground truth, at several steps.

*Risk:* high. It touches all three generators, the query engine every
dashboard depends on, and the dashboard's navigation model (R-18). It is
no longer blocked.
*Scheduling:* **build M20 first.** M19 adds the collection step to every
generator. Doing it once, across all three, proves the change generic
(FR-EV4), rather than retrofitting the two smaller generators later.

---

### Phase 3, continued — Analytics

---

**M20 · Remaining dashboards** *(was M11)*

License Optimization and Application Portfolio Rationalization, each a
generator plus a hierarchy descriptor plus a dashboard descriptor.

*Discharges:* FR-AN7, and demonstrates FR-EV4
*Exit:* both dashboards work with **no new UI code and no new backend
query code**. Any UI code written here is evidence that M9's schema was
under-specified.
*Contingency:* under D-1 the degradation path is a thinner descriptor,
not a different build. Cheaper than the earlier hand-built plan assumed.
*Rework note:* the dashboards render in the Life pane (D-14), which
changes where they appear and nothing about how they are built. This
milestone has no dependency on Phase R and can run at any point after
M10. It **must precede M19**, which extends all three generators with
the collection step (D-17).

---

### Phase 4 — Craft

---

**M21 · Design pass** *(was M12)*

Final tokens, both themes, typography, motion, chart palettes with
contrast validation in both themes. **Now also covers what Phase R
added:** the pane shell and layout control, the growth tree's motion
budget (R-14), the routing-problem treatment, and the Life pane,
including how a pinned view shows that newer collections exist (R-18).
OQ-3, the accent colour and typeface, is still settled here. Visual
continuity with the Agent One demo is deferred (OQ-13), so it does not
constrain this pass.

*Discharges:* NFR-V1–V6
*Exit:* both themes pass contrast checks and the interface reads as
analytical infrastructure rather than an AI console.
*Note:* this is a deliverable, not optional polish. See R-6.

---

**M22 · Rehearsal and hardening** *(was M13)*

Operator control concealment, beat-timing calibration against the 270 s
target (D-8, OQ-7), an automated determinism test comparing modulo
timestamps and durations (A-2), full narrative runs. **Calibration now
includes the closing beats** (R-15), and the Life pane's collection
clock and recalibration interval (D-17). The determinism test also covers the growth tree's final
state (FR-G5).

*Discharges:* FR-O2, NFR-D1–D4, NFR-P3–P5, and the §7 acceptance
criterion
*Exit:* two consecutive runs from Reset produce identical output under
A-2's definition, and the full narrative runs cleanly without touching a
terminal. Confirm OQ-4 here: measure whether the stream needs
virtualisation rather than assuming it does not.
*Outcome:* met. The 1x rehearsal took 268 s of narrative against 270 s,
and two runs from Reset matched under A-2, the growth tree included
(`tests/test_rehearsal.py`). Two defects were fixed: a capital letter
typed into the credential form fired an operator shortcut, and the
engine ran slow under load. OQ-4 closed: no virtualisation. `pytest`
gives 561 passed. Details in `project-notes.md` §84.5.

---

## 4. Critical path

Built:

```
M0 → M1 → M2 ──┬─→ M3 ─→ M4 ─→ M5 ─→ M6 ─→ M7 ─→ M8 ─┐
               └─────────────────────→ M9 ─→ M10 ─────┴─→ (built)
```

Then, also built, in this order:

```
M11 → M12 → M13 → M14 → M15 → M16 → M17 → M18 ─┬─→ M19 → M21 → M22
                                                 │
       M20 ──────────────────────────────────────┘
       (no dependency on Phase R; any time after M10, but before M19)
```

M20 was built after M18 and before M19, as planned. Nothing remains.

The renames (M11 to M13) come first because they are cheap and touch no
logic. They also leave the vocabulary settled before the move, so M14
relocates components already carrying their final labels. M14 comes
before all the new features, because M15 to M19 each put something into
one of the two panes.

Among the new features, M15, M16 and M17 do not depend on one another,
and the order among them is by risk. M18 needs M14, because it hands the
layout over to Life. M19 needs M18, because collection begins where
seeding closes. **M19 also needs M20**, because it extends all three
generators, and extending three at once is what proves the change
generic. M20 depends on nothing in Phase R, so it can be done whenever
there is room, as long as it lands before M19.

M10 preceded the remaining dashboards deliberately, and still does:
M10 proved the schema against the demanding case, and M20 confirms the
generality claim.

---

## 5. Decisions --- ruled

Full reasoning, measurements and consequences are in `decisions.md`. The
rulings themselves:

| ID   | Ruling | Note |
| ---- | ------ | ---- |
| **D-1** | **Fully descriptor-driven dashboards.** The backend serves chart specifications; one generic renderer draws all three dashboards, including Ticket Anomaly. | Conforms to FR-EV4 literally, so **R-1 needs no amendment**. Moves significant work into M9 and raises R-2 and R-6. |
| **D-2** | **pandas.** | Measured: the largest dataset builds in 0.108 s and a two-key groupby costs 6 ms. Performance is not a differentiator here, so familiarity decides. |
| **D-3** | **URL-synced filter context**, Pinia as the in-memory mirror. | Back works on drill state, and rehearsal can jump straight to a view --- which the tight OQ-7 target makes necessary. |
| **D-4** | **Hand-authored graph coordinates.** | Deterministic; reads as designed at ~30 nodes. Lives beside `acme.py`. |
| **D-5** | **Derive the ECharts theme from CSS custom properties at runtime.** | Chart specs carry semantic colour roles, never hex. Contains R-4. |
| **D-6** | **Parity test** between `protection.md` and the Python rule set. | Folded into D-7's suite. |
| **D-7** | **Determinism, state machine, query engine**, plus the D-6 parity test. | Covers what a live demo can fail on, without spending M21's time. |
| **D-8** | **Total-duration budget**, beats carry relative weights. | Mandatory rather than convenient under a 4--5 minute target. |
| **D-9** | **Unbounded event log** within a run. | FR-E7 needs exact replay; OQ-7's duration bounds the volume anyway. |
| **D-10** | **uv.** | Already installed on the target machine (0.12.8), which removes its only cost. |
| **D-11** | **Renames are display-only.** Identifiers, keys, paths, event types and request ids keep their names. **Agent One VW** names what grows out of the Seed; Agent Components are its parts. Methodologies keep their name. | The Seeding and Life rework. Glossary in §2. OQ-8 and OQ-9 answered. |
| **D-12** | **Potential** keeps the four computed grades with new meanings, plus a **routing-problem flag** beside the grade. | The flag is computed from facts, never authored. OQ-10 confirmed. |
| **D-13** | **Planting shows the declared stack**, marked unverified. | Resolves the conflict with G-2: what the seed was told, not what exists. |
| **D-14** | **Two panes, Seeding and Life**, both mounted; the lifecycle sets the default layout. | The seed screen stays full-screen until planted. |
| **D-15** | **A growth tree replaces the lifecycle strip** in the Seeding pane; protection decisions water it. | No gen-AI calls exist to water it (NFR-D1). OQ-11 confirmed. |
| **D-16** | **Closing the seeding phase** is a new lifecycle state, confirmed by a person, with three simulated, policy-gated operations. | Needs new protection rules; the only Phase R milestone that edits a test assertion. |
| **D-17** | **Life is time-revealed operation** (Option B, OQ-12): a finite collection cursor over already-generated data, with precomputed recalibration. A drilled-in view pins to its step. | The "maintaining" half of Agent One VW. Needs A-8 and A-9. |
| **D-18** | **The growth tree grows in the Life pane**, vertically from seed to tree as the process advances, then hands over to Agent One VW. The strip returns to the Seeding pane; Life only is the default during the build. | Ruled after M17's review. Amends D-15 and D-14's layout. A-10 to A-12. |
| **D-19** | **Both during the build**, and the grown tree kept behind a **Growth** control after the hand-over. The tree's stem ages from green to bark, and it gains texture, leaf cover and denser roots. | Ruled after D-18's review. Amends D-18 and D-14's layout. A-13, A-14. |
| **D-20** | **Closing retires the build tools and consumes the seed**: a fourth, policy-gated operation, and the tree sheds its stake and seed husk as closing proceeds. | Ruled at M18. Amends D-16. A-15. |
| **D-21** | **`run.ps1` launches where uv is blocked**: pip into `.venv`, then `run.py`. `uv.lock` still pins the versions. | Recorded 2026-10-02 (`decisions.md` §8). Amends D-10. |
| **D-22** | **The product is displayed as Seed v0.1**, in the top bar, the page title, the API title and the launch banners. Identifiers keep their names. | Recorded 2026-10-02 (`decisions.md` §8). Display only, as D-11 rules. |

Two requirement amendments follow from D-1 to D-10 and are applied in
`requirements.md`:

- **A-1** --- NFR-P1 is measured on a warm interpreter. A cold
  `import pandas` alone costs 2.10 s, which no design decision removes.
- **A-2** --- NFR-D4 defines determinism modulo timestamps and durations.
  **This resolves R-7.**

The Seeding and Life rework adds thirteen more, A-3 to A-15, and the
as-built review one, A-16. Each supersedes or clarifies rather than
deleting (`decisions.md` §7.2, §8):

- **A-3** --- FR-L2 superseded by FR-L9, which adds `CLOSING_SEEDING`.
- **A-4** --- FR-L6 superseded by FR-G1: the growth tree is the
  lifecycle indicator.
- **A-5** --- FR-L8 superseded by FR-L10: return to the Life pane.
- **A-6** --- FR-I6 superseded by FR-C6: the ready list appears in Life
  after closing.
- **A-7** --- the §7 acceptance criterion includes closing, the Life
  pane, and watching Agent One VW collect and recalibrate.
- **A-8** --- §4.1's Evolution exclusion is clarified: recalibration
  within a run is not Evolution.
- **A-9** --- FR-AN4 superseded by FR-AN10: headline counts are those of
  the data collected so far.
- **A-10** --- A-4 reversed: FR-L6 stands again, and the lifecycle strip
  is the Seeding pane's indicator. FR-G1 places the tree in Life (D-18).
- **A-11** --- FR-W3: Life only is the default from planting until the
  build completes (D-18).
- **A-12** --- FR-W4: the Life pane shows the growing tree until the build
  completes, then Agent One VW (D-18).
- **A-13** --- FR-W3: supersedes A-11; Both is the default from planting
  until the build completes (D-19).
- **A-14** --- FR-W4: after the hand-over, a Growth control in the Life
  pane's header drops the grown tree open (D-19).
- **A-15** --- FR-C3, FR-C5: closing performs four operations; the fourth
  retires the build tools. Then the seed is consumed (D-20).
- **A-16** --- FR-G3, clarified as built: an escalated request waters,
  and a page load may play one pulse as the log replays (`decisions.md`
  §8).

---

## 6. Risks after the rulings

Status per risk; full reasoning in `decisions.md` §6.

> **Final status, at M22 (2026-10-02).** Every risk below is closed
> except two. R-12, two vocabularies, is a permanent cost of D-11 and is
> managed by its glossary. R-8 is accepted as built: the credential form
> validates nothing. The headings below keep the status each risk had
> while the build was under way; the closing status of each is in
> `decisions.md` §6 and §7.5.

### Resolved

**R-1 · FR-EV4 versus hand-built dashboards.** Resolved by D-1, which
conforms to the requirement instead of narrowing it. All three dashboards
are descriptor-driven, so a fourth methodology genuinely needs no new UI
code.

**R-7 · NFR-D4 unsatisfiable as written.** Resolved by amendment A-2:
determinism is defined modulo timestamps and durations. The M22 test
compares with those fields excluded.

**R-3 · NFR-P1 may not survive three generators.** Closed by
measurement. The largest dataset builds in 0.108 s against a 2 s budget.
The real startup cost is library import, addressed by A-1.

**R-10 · Beat timing uncalibrated.** Closed by OQ-7's answer of 4--5
minutes and D-8's budget model.

### Live

**R-2 · The dashboards dominate the schedule.** — *High / High, raised.*
D-1 moves the dashboard machinery into M9 and makes it the schedule's
single point of failure rather than merely its pivot. Mitigated by
settling OQ-1 first and designing the schema against the hardest chart
set. Trigger for concern: M9 slipping, or M10 requiring UI code that is
specific to Ticket Anomaly.

**R-6 · The differentiation is craft, not architecture.** — *Medium /
Very high, raised.* Under D-1 the craft must be expressible as data.
Emphasis, span, ordering, annotation and empty states have to be
descriptor fields, or the renderer produces a generic dashboard that no
M21 effort recovers. This is now an M9 schema-design concern as much as
an M21 one.

**R-4 · Dual theme doubles chart styling work.** — *Medium / Medium,
reduced.* D-5 makes contrast validation a per-token concern rather than a
per-chart one. Residual risk remains a design problem: a palette that
reads well dark can look washed out light.

**R-5 · Event-sourced state can drift from snapshots.** — *Low / High,
unchanged.* Largely designed out by snapshot-then-stream and the
sequence-gap check. D-7's state-machine suite should cover reducer parity
against the snapshot.

**R-8 · The credential form has nothing to validate.** Unchanged.
Validate shape --- non-empty, plausible URL --- and show a brief simulated
handshake, so obvious junk is rejected even though acceptance is
unconditional.

**R-9 · FR-S5 and FR-S6 sit close together.** Unchanged. A headingless
seed file yields an empty but successful summary. Give it a sensible
empty state.

### New

**R-11 · A 4--5 minute narrative is tight.** — *Medium / Medium.* Four
phases inside 270 s leaves little room per beat. Mitigated by grouped
node bursts at M6, a denser and shorter activity stream, and protected
weights for the credential pause and timeout recovery. Raising the total
during rehearsal is a single number (D-8), so treat 270 s as a target
rather than a constraint.

### New in the Seeding and Life rework

Full entries in `decisions.md` §7.5.

**R-12 · Two vocabularies.** — *Certain / Low.* The code says
`solution` and the screen says "Agent Component". D-11's glossary is the
mitigation, and new code keeps the code vocabulary.

**R-13 · Silent-failure renames.** — *Medium / Medium.* CSS selectors
keyed to grade values and the cross-boundary request id
`'solution-approval'` break with no type error and no failing test.
M12's audit classifies them before M13 changes anything. The exit
criteria of M11 and M13 include hand checks of grade colours and of the
approval flow.

**R-14 · The growth tree reads as decoration or as an "AI toy".** —
*Medium / High.* The technical risk is low and the design risk high.
Every segment and every watering step is tied to an event (D-15), the
motion budget is a requirement (NFR-V7), and M21 reviews it.

**R-15 · Closing lengthens a tight narrative.** — *Medium / Medium.*
Closing carries a fixed D-8 weight, and M22 recalibrates the total.

**R-16 · Unconfirmed stakeholder terms.** — *Closed.* OQ-8 to OQ-12
were answered and OQ-13 deferred before any milestone built on them.

**R-17 · "Self-improving" meets the Evolution exclusion.** —
*Resolved.* D-17's recalibration is precomputed and finite, so
determinism holds (A-2), and A-8 states why it is not Evolution.

**R-18 · Two cursors confuse.** — *Medium / Medium.* The system cursor
advances while a drilled-in view stays pinned, so a viewer may not
realise they are looking at an earlier step. The pinned view always says
how many collections are newer, and the evidence panel names its
calibration. M21 designs the treatment.

---

## 7. What is still open

Nothing. The build is complete and accepted (2026-10-02). OQ-3 was
settled at M21: a cobalt accent, and Inter with JetBrains Mono, bundled
with the build. See `decisions.md` §4.
OQ-8 to OQ-13, raised by the Seeding and Life rework, are all closed:
five answered and one deferred. Answers are in `decisions.md` §7.4.

Closed: OQ-1 (chart inventory: KPIs, treemap, bar, line, subset and
record tables, colour bound to pattern), OQ-2 (the two smaller
hierarchies), OQ-3 (cobalt; Inter and JetBrains Mono), OQ-4
(no virtualisation, measured at M22), OQ-5 (no cache), OQ-6 (DENY PR-033,
ESCALATE PR-053), OQ-7 (4--5 minutes). See `decisions.md` §4 and §5.
