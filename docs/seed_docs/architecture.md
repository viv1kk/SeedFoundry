# Seed v0.1 --- Architecture, as built

> **Status:** Reference for the system as built at M22 (commit `6a7be84`),
> written 2026-10-02 from the code. Where this document and the code
> disagree, the code is right and this document is out of date.
>
> **Related documents:** `requirements.md` says what the system must do,
> `decisions.md` why it is built this way, and `implementation-plan.md`
> how it was built, milestone by milestone. This document says what is
> there now. The visual language is in `design-system.md`, and running
> the demo is in `operator-guide.md`.

---

## 1. Shape

Two processes on one machine, started together by `run.py` (NFR-L1):

| Process | Address | What it is |
| ------- | ------- | ---------- |
| Backend | `http://127.0.0.1:8000` | FastAPI under uvicorn. Every route is under `/api`. |
| Frontend | `http://localhost:5173` | Vite's dev server for the Vue 3 app. It proxies `/api` to the backend, so the browser sees one origin and the event stream needs no CORS. |

Vite binds to localhost only, and `127.0.0.1:5173` does not answer. The
ports are constants in `backend/app/config.py` and in
`frontend/vite.config.ts`, not configuration (NFR-D3).

There is one run per backend process. `runtime.py` holds the single
`SystemState`, the `EventBus` that fans its events out to open streams,
and the `EventSource`, which is the simulation engine. Every browser
connected to the backend watches the same run. Nothing persists: a
restart, or Reset, starts again from the seed screen (FR-L7).

The datasets are generated in the FastAPI startup hook, before the
health check answers. `run.py` imports the backend before it announces
readiness (A-1), and waits for both servers to answer.

The real and simulated sides of §3 of the requirements sit in separate
packages (NFR-A4): `simulation/`, `environment/`, and the generators in
`analytics/generator/` are the simulated side. `domain/`, `protection/`,
`knowledge/`, `analytics/` (query, store, evidence, schema) and `api/` are
built for real.

---

## 2. Two vocabularies

The screen and the code use different words for some things (D-11). The
code keeps its names everywhere: types, payload keys, API paths, event
types and request ids.

| Code | Screen |
| ---- | ------ |
| product | **Seed**, labelled **v0.1** (D-22) |
| the built solutions, as a whole | **Agent One VW (ValueWise™)** |
| solution, `Solution`, `solutionId` | **Agent Component** |
| `Phase.INIT` | **Planting** |
| `Phase.RUNTIME` | **Life** |
| feasibility, `Grade` | **Potential** |
| `appearsFeasible` | "Evidence located" |
| `CLOSING_SEEDING` | **Cleanup** |
| methodology | methodology (unchanged) |

Identifiers that still carry the working name "Systems" are kept: the
Python project `systems-v1`, the npm package `systems-v1-frontend`, and
the theme's storage key `systems-v1.theme`.

---

## 3. Lifecycle

`domain/lifecycle.py` declares twelve states and one transition table.
An illegal move raises `IllegalTransition`, which the API returns as a
409 (FR-L3).

| State | Phase | Moves to |
| ----- | ----- | -------- |
| `UNINITIALIZED` | INIT | `INITIALIZED` (the plant, over HTTP) |
| `INITIALIZED` | INIT | `DISCOVERING` |
| `DISCOVERING` | DISCOVERY | `DISCOVERY_BLOCKED`, `DISCOVERY_COMPLETE` |
| `DISCOVERY_BLOCKED` | DISCOVERY | `DISCOVERING` |
| `DISCOVERY_COMPLETE` | DISCOVERY | `ASSESSING` |
| `ASSESSING` | ASSESSMENT | `AWAITING_APPROVAL` |
| `AWAITING_APPROVAL` | ASSESSMENT | `IMPLEMENTING` |
| `IMPLEMENTING` | IMPLEMENTATION | `IMPLEMENTATION_COMPLETE` |
| `IMPLEMENTATION_COMPLETE` | IMPLEMENTATION | `CLOSING_SEEDING` |
| `CLOSING_SEEDING` | IMPLEMENTATION | `READY_TO_RUN` |
| `READY_TO_RUN` | RUNTIME | `RUNNING` |
| `RUNNING` | RUNTIME | `READY_TO_RUN` |

Reset is not an edge. It cancels the run and rebuilds System State from
nothing. Waiting on a person is the `blockedOn` flag beside the state,
not a state of its own (FR-L4).

Agent Components have their own table (`domain/solutions.py`):
`PROPOSED → AWAITING_APPROVAL → APPROVED → BUILDING → READY ⇄ RUNNING`,
with `REJECTED` terminal (FR-AP2).

---

## 4. The run

The engine (`simulation/engine.py`) walks five workflows in order
(`workflows/registry.py`). Each is a generator that records events into
System State and yields beats.

| Workflow | From → to | Weight | Waits on a person |
| -------- | --------- | ------ | ----------------- |
| discovery | `INITIALIZED` → `DISCOVERY_COMPLETE` | 54 | Credentials for the ServiceNow Incident API |
| assessment | → `AWAITING_APPROVAL` | 25 | One approval per Agent Component |
| implementation | → `IMPLEMENTATION_COMPLETE` | 20 | --- |
| closing | → `READY_TO_RUN` | 6 | The confirmation that closes seeding |
| life | stays in `READY_TO_RUN` | 0 | --- |

The narrative's 105 units are scaled to 270 seconds at 1x
(`config.TOTAL_DURATION_SECONDS`, `NARRATIVE_WEIGHT`), so one unit is
about 2.57 s. A beat may also carry a floor in seconds, which protects
the credential acceptance and the timeout recovery from being compressed
out of sight. Life's beats weigh nothing and use their floors alone: 3 s
a collection step and 2 s more per recalibration.

Speed divides every remaining delay by 1 or 2, and instant removes it,
floors included. Skip removes delays until the phase changes. Both act
on the next slice of a beat, within 50 ms (FR-O3).

### Requests to a person

| Request id | Kind | Answered by | Body |
| ---------- | ---- | ----------- | ---- |
| `servicenow-incident-api` | credentials | `POST /api/human/{id}` | `{ "username", "password" }`. Nothing is validated. The values are used for the handshake and discarded (FR-H5); only the field names are recorded. |
| `solution-approval` | approval | `POST /api/solutions/{id}/decision` | `{ "decision": "approve" \| "reject" }`. The request is asked again while any Agent Component awaits a decision, so a full run raises it three times. |
| `close-seeding` | confirmation | `POST /api/human/{id}` | `{ "acknowledged": true, "choice": "close" }`. The one option is labelled "Run — clean up and close seeding" (FR-C1). |

`ambiguity` and `missing-info` are defined and styled, but the scripted
run raises neither.

### What a full run records

With every component approved, a run records 140 events by the time Life
is caught up: 3 in the Planting phase, 42 in Discovery, 23 in
Assessment, 53 in Implementation and Cleanup, and 19 in Life. Running a
dashboard and returning add one event each, which is why M22 counted 142
entries in the stream. 34 events are policy decisions: 32 ALLOW,
1 DENY (PR-033, ServiceNow's security log) and 1 ESCALATE (PR-053,
deployment).

Discovery ends with "5 systems, 6 data sources, 17 datasets (16
profiled, 1 excluded by policy)". Assessment grades Ticket Anomaly
Detection HIGH, License Optimization PARTIAL and Application Portfolio
Rationalization MEDIUM, with one routing problem: APR's usage signal in
the refused security log.

---

## 5. Events

Every event has `sequence` (contiguous from 1 within a run), `timestamp`,
`type`, `phase` (taken from the lifecycle when it is recorded),
`category`, `severity`, `message` and `payload`. The SSE frame's `id` is
the sequence and its `event` is the type, so the browser replays from
`Last-Event-ID` on reconnect (FR-E7). An idle stream sends a keepalive
comment every 15 s.

Categories (FR-E4): `DISCOVERY`, `ANALYSIS`, `VALIDATION`, `DECISION`,
`POLICY`, `WARNING`, `SUCCESS`, `HUMAN_INPUT`. Severities: `INFO`,
`WARNING`, `ERROR`.

Event types, by where they come from:

| Source | Types |
| ------ | ----- |
| State and plant | `lifecycle.transition`, `seed.loaded`, `human.requested`, `human.resolved`, `run.failed` |
| Discovery | `system.ready`, `discovery.inventory.loaded`, `discovery.system.found`, `discovery.endpoint.testing`, `discovery.credentials.required`, `discovery.credentials.accepted`, `discovery.datasets.enumerated`, `discovery.dataset.excluded`, `discovery.system.connected`, `discovery.endpoint.timeout`, `discovery.endpoint.recovered`, `discovery.system.registered`, `discovery.completed` |
| Protection | `policy.decision` |
| Assessment | `assessment.methodology.evaluated`, `assessment.evidence.insufficient`, `assessment.evidence.revised`, `assessment.completed`, `solution.proposed`, `solution.submitted`, `solution.approved`, `solution.rejected`, `approval.completed` |
| Implementation | `implementation.started`, `implementation.build.started`, `implementation.component.built`, `implementation.tests.passed`, `solution.ready`, `implementation.completed` |
| Cleanup | `seeding.closing.started`, `seeding.notes.consolidated`, `seeding.scratch.cleared`, `seeding.interfaces.promoted`, `seeding.tools.retired`, `seeding.consumed`, `deployment.ready` |
| Life | `life.collection.started`, `life.collection.step`, `life.recalibrated`, `life.caught_up` |
| Running | `solution.started`, `solution.closed` |

The frontend subscribes to each type by name (`stores/events.ts`), and
`tests/test_frontend_contract.py` fails if the backend emits a type the
list lacks.

How an entry is presented is derived from its type by suffix
(`domain/presentation.py`, mirrored in `design/presentation.ts`): a type
ending `.insufficient`, `.unresolved` or `.withheld` is an
insufficiency; one ending `.failed`, `.timeout`, `.error` or
`.unreachable`, or of severity ERROR, is a fault; a `HUMAN_INPUT` event
is a decision; everything else is activity. A policy denial is never a
fault (FR-H4).

---

## 6. Analytics

Three dashboards, one per methodology. Each is a generator in
`analytics/generator/` and a descriptor in `analytics/descriptors/`,
drawn by one renderer (`views/DashboardView.vue`, D-1).

| Solution id | Title | Records |
| ----------- | ----- | ------- |
| `ticket-anomaly-detection` | Ticket Intelligence | 184,392 tickets |
| `license-optimization` | Licence Utilisation | 13,620 seats, and 163,440 seat-months of activity |
| `application-portfolio-rationalization` | Application Portfolio | 186 applications, and 2,232 application-months of usage |

All three cover September 2025 to August 2026 from fixed seeds (NFR-D5).
Every figure is aggregated from rows at request time (FR-AN5), and every
answer carries the milliseconds it took.

### The filter context

```
{ timeRange?: [date, date], dimensions: { id: [values] }, entityId?: string, step?: 0..12 }
```

Values within a dimension are alternatives, and dimensions combine.
`step` is Life's collection step: only records collected by then exist,
and figures are read under the calibration in force at that step. No
step means the full dataset. The interface expresses a time range as a
brushed run of months, which is a `month` dimension filter, so it never
sends `timeRange`; the API accepts it.

### The URL

The open dashboard and its drill path live in the query string (D-3):

```
/?dashboard=<solution id>&drill=<JSON list of drill steps>&step=<n>
```

Each drill step is `{ "label", "dimensions"?, "entityId"? }`, and the
filter is the steps folded in order. `step` is present only while the
view is pinned. A link with `dashboard` and no run open opens the
dashboard as a rehearsal, in the Life pane. The browser's Back pops one
drill step.

### Life's clock

`analytics/generator/__init__.py` holds it. Collection covers the final
twelve weeks, ISO weeks 24 to 35 of 2026 (from 8 June), one week a step.
Calibration 0 is what Life starts with, and a recalibration falls every
four steps, so there are three. Every frame carries a `collected` column
naming the step its row arrives at. Recalibrated columns, and what each
recalibration moved, are computed at startup (FR-AN3). A ticket cluster
is confirmed once 60% of its tickets have arrived, and scored at 0.75 of
its score until then.

---

## 7. API

Every path is under `/api`. A refusal by the state machine or the engine
is a 409 with a `detail`; a rejected seed layer is a 400 naming the
layer and the reason.

| Method | Path | Purpose |
| ------ | ---- | ------- |
| GET | `/health` | Readiness, which `run.py` polls |
| GET | `/state` | The full snapshot, with the sequence it is current as of (FR-E5) |
| GET | `/events` | The SSE stream, replaying from `Last-Event-ID` |
| GET | `/seed/layers` | The three slots: layer, filename, the question each answers |
| POST | `/seed/parse` | Validate and summarise one layer, committing nothing (FR-S4, FR-S5) |
| GET | `/seed/bundled` | The repository's seed files (FR-S7) |
| POST | `/seed/initialize` | Plant all three layers and move to `INITIALIZED` |
| GET | `/operator` | Run status and speed |
| POST | `/operator/start` | Start the run, from `INITIALIZED` only |
| POST | `/operator/speed` | `{ "speed": "1x" \| "2x" \| "instant" }` |
| POST | `/operator/skip` | Drop delays until the phase changes |
| POST | `/operator/reset` | Clear the run; back to `UNINITIALIZED` |
| POST | `/human/{request_id}` | Answer the request the run is parked on |
| POST | `/solutions/{id}/decision` | Approve or reject one Agent Component |
| POST | `/solutions/{id}/run` | Open a ready component (`READY_TO_RUN → RUNNING`) |
| POST | `/solutions/{id}/close` | Return from it (`RUNNING → READY_TO_RUN`) |
| POST | `/environment/sources/{dataset}/fields/{field}` | Revise a profiled field's completeness and regrade (rehearsal, M7) |
| GET | `/protection/rules` | The rule set, grouped as `protection.md` groups it |
| POST | `/protection/evaluate` | A dry run: what the engine would decide, recording nothing |
| GET | `/analytics` | The dashboards |
| GET | `/analytics/{id}/dashboard` | The descriptor, its value domains and colour roles, and Life's clock |
| POST | `/analytics/{id}/query` | `{ filter, views? }` → every view's figures |
| POST | `/analytics/{id}/records` | One page of a record table |
| POST | `/analytics/{id}/evidence` | The evidence for the finding a filter narrows to (FR-EV7) |

FastAPI's own `/docs` page lists the same routes, titled "Seed v0.1".

---

## 8. Protection

`protection/rules.py` is the rule set, and `seeds/protection.md` is its
readable form. `tests/test_protection.py` holds the two equal, row for
row (D-6, FR-P7).

| Group | Rules |
| ----- | ----- |
| Default | PR-000 |
| Identity and authentication | PR-010 to PR-014 |
| Credentials | PR-020 to PR-025 |
| Data access | PR-030 to PR-036 |
| Data movement | PR-040 to PR-044 |
| Write and destructive operations | PR-050 to PR-055 |
| Agent capability | PR-060 to PR-064 |
| Evidence integrity | PR-070 to PR-076 |
| Auditability | PR-080 to PR-082 |
| Closing the seeding phase | PR-090 to PR-096 |

52 rules in all. A request states an action, a resource and facts, and
never names a rule. Every rule covering the action whose facts hold is
matched; the strictest effect wins (DENY over ESCALATE over ALLOW), and
the most specific rule of that effect is cited. A request that leaves
out a fact some rule for its action depends on is denied under PR-000,
and so is an action no rule covers.

Workflows proceed only on an ALLOW (`workflows/gate.py`, PR-082), except
where a refusal is expected: discovery leaves the security log out of
the model under PR-033 and carries on.

The granted tools are enumerated in `protection/capabilities.py`: the
test runner. Cleanup retires the build tools, the component generator
and the test runner, under PR-095.

---

## 9. Frontend

| Store | Holds |
| ----- | ----- |
| `system` | The snapshot, and the reducers that fold each event into it |
| `events` | The SSE connection, the event list, gap detection and re-snapshot (FR-E6), and the calls that answer requests |
| `layout` | Both, Seeding or Life; the lifecycle default; the leading pane |
| `dashboard` | The open dashboard, its drill steps, the pinned step, and the URL |
| `protection` | The rule set from `/api/protection/rules` and the decisions from the stream |
| `seed` | The seed screen's three slots, parsed as each file lands |
| `operator` | Run status and speed, the hidden panel, evidence revision |
| `theme` | Light or dark, on `<html data-theme>` |

`App.vue` shows the seed screen until the lifecycle leaves
`UNINITIALIZED`, or a rehearsal link names a dashboard. After that it
shows the top bar and both panes. Both panes stay mounted, and a layout
change only hides one (NFR-A7).

The default layout follows the lifecycle: Both from planting until
seeding closes, then Life only from `READY_TO_RUN`. A person's choice
holds until the default next changes. A pending request turns Life only
into Both (FR-W5), and a rehearsal link sets Life only (FR-W6).

The growth tree is `design/growth.ts`'s `growthOf(events)`, a pure
function of the event log, drawn by `components/GrowthTree.vue` (FR-G5).

---

## 10. Tests

`backend/tests`, 561 tests in 17 files, run with
`python -m pytest -q` from the repository root. There is no frontend
test runner (D-7); the frontend is checked by `npm run typecheck` and
`npm run build`, by `test_frontend_contract.py`, and by
`test_rehearsal.py`, which bundles `growth.ts` with esbuild and runs it
under Node.

| File | Covers |
| ---- | ------ |
| `test_lifecycle.py` | Every legal transition succeeds and every illegal one raises (D-7) |
| `test_events.py`, `test_engine.py` | The event log, replay, the beat runner, speed, skip and reset |
| `test_seed.py`, `test_declared.py` | The loader, the plant, and the declared stack |
| `test_protection.py` | The engine, and parity with `protection.md` (D-6) |
| `test_discovery.py`, `test_assessment.py`, `test_routing.py` | The narrative's first half, the grades and the routing problem |
| `test_implementation.py`, `test_closing.py` | The builds and cleanup |
| `test_analytics.py`, `test_life.py` | The query engine against row-level ground truth, and Life's steps (D-7) |
| `test_presentation.py`, `test_frontend_contract.py` | How events are presented, and the frontend's subscription list |
| `test_design.py` | WCAG contrast of every token pair, in both themes (NFR-V3) |
| `test_rehearsal.py` | Two runs from Reset over HTTP, equal under A-2, the tree included; timing; no outbound host; no model library |

One timing test, `test_any_filter_answers_every_view_inside_200_ms`, can
fail under heavy machine load. That was ruled noise, not a defect, on
2026-09-24 (`project-notes.md` §84.5, M15).
