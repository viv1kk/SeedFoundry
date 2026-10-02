# Seed v0.1 --- Design system, as built

> **Status:** Reference for the visual language as built at M22, written
> 2026-10-02 from `frontend/src/design/tokens.css`, the component styles
> and screenshots of a full run in both themes. The source of truth is
> `tokens.css`. If a value here disagrees with it, the file is right.
>
> **Requirements:** NFR-V1 to NFR-V7. **Rulings:** D-5 (chart colours
> from tokens), OQ-3 (accent and type, settled at M21), D-12 (Potential's
> colours), D-15, D-18 and D-19 (the growth tree), M21's design pass.

---

## 1. Principles

The interface should read as **serious analytical infrastructure, not an
AI toy** (NFR-V6). In practice that means five rules, each of which the
build follows:

1. **Colour carries meaning, never decoration.** Every colour in the app
   is a token with a stated role. A value that means something, such as
   an anomaly pattern or a utilisation class, has one colour on every
   chart, table chip and evidence panel (OQ-1).
2. **Fault colour is for faults.** Red appears only for a technical
   error, a refused request's verdict, and findings drawn as anomalies.
   A request for a person's input is never red or amber, because nothing
   has gone wrong (FR-H4).
3. **Weight, not movement, shows state.** Complete, current and future
   phases differ in weight and colour. Animation marks a real change
   and stops when the change has landed (NFR-V5).
4. **Dense, not cluttered.** Small type, a monospace face for figures and
   identifiers, thin borders instead of heavy cards (NFR-V1).
5. **Nothing generic-AI.** No gradients as decoration, no glow except
   the tree's watering pulse, no robot or agent illustration, no
   futuristic styling (NFR-V4).

---

## 2. Themes

Two themes, light and dark, from one token file (NFR-V2). Light values
sit on `:root`; dark overrides the same names under
`[data-theme='dark']`, which the theme store sets on `<html>`. No
component knows which theme is showing.

- **First visit:** the theme follows the operating system's
  `prefers-color-scheme`.
- **Toggle:** Shift+D, or the operator panel. The choice is kept in the
  browser under `systems-v1.theme` and wins over the system setting from
  then on.
- Charts re-resolve their colours when the theme changes (D-5).

The comment at the top of `tokens.css` calls light the default. It is the
fallback when nothing else decides.

---

## 3. Colour

### Surfaces, lines and text

| Token | Light | Dark | Use |
| ----- | ----- | ---- | --- |
| `--surface-base` | `#f7f8fa` | `#0e1116` | Page and pane background |
| `--surface-raised` | `#ffffff` | `#161b22` | Cards, top bar, panels |
| `--surface-sunken` | `#eef0f4` | `#090c10` | Inputs, drop zones, wells |
| `--surface-overlay` | `#ffffff` | `#1c222b` | Drawers and overlays |
| `--border-subtle` | `#e2e5eb` | `#21272f` | Dividers |
| `--border-default` | `#cbd0d9` | `#2f3742` | Card and control borders, the pane divider |
| `--border-strong` | `#9aa2b1` | `#4a5461` | Emphasised outlines |
| `--text-primary` | `#12151b` | `#e8ebf0` | Body text and figures |
| `--text-secondary` | `#4a5261` | `#a8b1bd` | Supporting text |
| `--text-muted` | `#666e7a` | `#808995` | Labels, hints, timestamps |
| `--text-inverse` | `#f7f8fa` | `#0e1116` | Text on filled controls |

Scrollbars are thin, drawn in `--scrollbar-thumb` on a clear track, in
both themes.

### Accent and status

| Token | Light | Dark | Means |
| ----- | ----- | ---- | ----- |
| `--accent` | `#1e61f5` | `#5b8cff` | Cobalt (OQ-3). Primary actions, the current phase, a request awaiting a person, work in progress |
| `--accent-subtle` | `#ebf1fe` | `#15203a` | Selected rows, a node awaiting input, a component building |
| `--status-positive` | `#1b7d4a` | `#3fb27a` | Done, validated, connected, allowed, approved |
| `--status-warning` | `#9a6100` | `#d79a3a` | Caution: an escalation, PARTIAL potential, a pinned view |
| `--status-negative` | `#c0392f` | `#e5705f` | A fault, and a DENY's verdict |
| `--status-neutral` | `#5a6172` | `#808995` | A state of knowledge: insufficient evidence, unverified |

### Potential (D-12)

An ordered scale from strong value to not yet modellable. PARTIAL is
the caution colour and never the fault colour.

| Grade | Token | Light | Dark |
| ----- | ----- | ----- | ---- |
| HIGH | `--grade-high` | `#1b7d4a` (positive) | `#3fb27a` |
| MEDIUM | `--grade-medium` | `#597718` olive | `#8aab4c` |
| PARTIAL | `--grade-partial` | `#9a6100` (warning) | `#d79a3a` |
| LOW | `--grade-low` | `#5a6172` (neutral) | `#808995` |

### Chart roles (D-5)

Chart specifications name a role, and the renderer reads
`--chart-<role>` at paint time. No descriptor contains a hex value.

| Role | Light | Dark | Bound to, in the dashboards |
| ---- | ----- | ---- | --------------------------- |
| `series-1` | `#1e61f5` | `#5b8cff` | Resolution stall; Consolidate; assigned seats |
| `series-2` | `#6b4fd8` | `#9a82f0` | Reopen churn |
| `series-3` | `#0c7f7f` | `#35b8b8` | Priority mismatch |
| `series-4` | `#a16500` | `#d79a3a` | Volume burst |
| `series-5` | `#b8437c` | `#e06fa8` | Reassignment loop |
| `series-6` to `series-8` | `#5d7c19`, `#8a5a2b`, `#3d6f8f` | `#9cc95a`, `#c49a6c`, `#7fb0d0` | Cluster colours, cycled within one pattern |
| `positive` | `#1b7f4b` | `#3fb27a` | Active seats; Retain |
| `warning` | `#9c671a` | `#e0a84a` | Underused seats; Replace |
| `negative` | `#c0392f` | `#e5705f` | Leaver seats |
| `anomaly` | `#cc431e` | `#ff7a4d` | Anomalous tickets; Unused seats; Retire; the primary KPI's top rule |
| `baseline` | `#8c95a6` | `#5b6777` | Normal or total series |
| `muted` | `#cbd0d9` | `#2f3742` | Normal tickets; Unassigned seats; Unresolved applications |

`--chart-grid` and `--chart-brush` draw the grid and the brushed range.

### Where each state takes its colour

| Surface | State | Treatment |
| ------- | ----- | --------- |
| Human-input surface | credentials | Left rule in accent |
| | approval, confirmation | Left rule in positive |
| | ambiguity, missing-info | Left rule in warning (defined, unused in the run) |
| Activity stream | activity | Plain |
| | decision (human input) | Accent rule and category |
| | fault | Negative rule, category and message |
| | insufficiency | Neutral rule and category, secondary message |
| | policy ALLOW / DENY / ESCALATE | Verdict in positive / negative / warning. A DENY's left rule is secondary text and an ESCALATE's is warning |
| Environment graph | unknown | Muted, unfilled |
| | testing | Dashed halo |
| | requires-input | Accent, with a halo |
| | validated / connected | Positive outline / positive fill |
| | error | Negative outline, halo and label |
| Build pipeline | PENDING | Dashed box |
| | BUILDING | Accent box on accent-subtle, with a flowing edge |
| | TESTING | Accent outline, with a sweep |
| | VALIDATED, COMPLETE | Positive |
| Agent Component card | routing problem | Dashed outline in secondary text and a ⤳ mark: neither a grade colour nor the fault colour |
| Dashboard | pinned view | "Pinned to week N · K newer collections" in warning, beside Catch up |
| | months still being collected | Shaded and labelled "Collecting"; the line stops at the cursor |

### The growth tree

Muted on purpose: it is a progress indicator, not an illustration
(R-14). Green above ground, earth brown below, a warm soil that fades
downward. The stem mixes `--growth-stem-young` into `--growth-bark` as
it ages (D-19). Water is `--growth-water` and `--growth-root-wet`, and
the pulse's glow is `--growth-glow`, the one glow in the app. A ready
component's fruit is `--growth-bud`, violet. The stake and its ties are
`--growth-stake` and `--growth-tie`. Each has a light and a dark value
in `tokens.css`.

---

## 4. Type

| Face | Use |
| ---- | --- |
| **Inter** (`--font-sans`) | Everything that is read as prose: headings, body, labels |
| **JetBrains Mono** (`--font-mono`) | Figures, identifiers, rule ids, lifecycle states, timestamps, the stream's categories, the version label |

Both are variable fonts, bundled from npm (`@fontsource-variable`) and
served with the app, never fetched from the network (NFR-D2). Segoe UI
and Consolas are the fallbacks.

| Token | Size | Typical use |
| ----- | ---- | ----------- |
| `--text-xs` | 11 px | Small capitals labels, timestamps, chips |
| `--text-sm` | 13 px | Supporting text, table cells, pane headings |
| `--text-md` | 15 px | Body (the default), and stage headings in semibold |
| `--text-lg` | 18 px | Drawer and panel headings, the Life pane's Agent One VW title |
| `--text-xl` | 24 px | KPI figures |
| `--text-2xl` | 32 px | The seed screen's title |

Small labels set in capitals carry wide letter-spacing (0.06 to 0.08 em).
Body line height is 1.5.

---

## 5. Space, shape and depth

- **Space** steps by 4 px: `--space-1` (4 px) to `--space-12` (48 px).
- **Radius:** 3 px for chips, buttons and small controls; 6 px for cards,
  KPI tiles, chart cards and build lanes; 10 px only for the seed
  screen's layer cards.
- **Depth:** two shadows, `--shadow-sm` and `--shadow-md`, used sparingly.
  Borders separate surfaces far more often than shadows do.

---

## 6. Layout

**The seed screen** is full-screen until the seed is planted (FR-W7):
the title "SEED", the line "Plant the methodology.", three layer cards
with a drop zone each, and Initialize.

**The top bar** is a three-column grid. The identity, "Seed v0.1", sits
left; the layout control (Both, Seeding, Life) is held at the centre
whatever the lifecycle label's length (M21); the raw lifecycle state, in
mono capitals, sits right. During closing it reads `CLEANUP`.

**The panes.** In Both, the pane where the work is happening takes
three fifths of the width: Seeding until the hand-over, Life after it
(M21). Below 64 rem wide, the two stack.

**The Seeding pane**, top to bottom: the lifecycle strip; the stage;
the human-input surface while a request is open; and the Activity and
Protection rail. In Seeding only, the rail is a column of 22 to 30 rem
beside the stage. In Both it docks along the bottom as a drawer, which
closes to a bar that still shows the newest entry.

**The Life pane:** a header with "Agent One VW (ValueWise™)", the
collection progress and the Growth control; then the growing tree, or,
after the hand-over, "Seeding complete" and the Live Agent Components,
each with its Potential, test count and Run. A dashboard opens over the
list inside the pane.

**A dashboard** has four bands (OQ-1): KPIs; a twelve-column chart grid
whose first chart spans the width; a focused table; and the record
table. The drill bar above them carries Back, the breadcrumb, the
collection state and the Evidence button. The evidence panel slides in
at the side.

---

## 7. Known limits, accepted

- **Both, during approval, at 1600 × 1000.** The approval surface sits
  under the stage and takes about a third of the pane, so the cards'
  Review and Approve buttons fall below the fold. The stage scrolls, and
  Seeding only shows them whole.
- **The environment graph while a request is open.** It is limited by
  height and draws at about half size, because the request has the
  viewer's attention then (M21).
- **A page load can play one watering pulse** as the replayed log
  arrives (A-16).

---

## 8. Motion

Durations come from three tokens: `--duration-fast` 120 ms,
`--duration-base` 220 ms, `--duration-slow` 400 ms, eased by
`--ease-out`. Every animation is tied to a state change (NFR-V5):

| Animation | When |
| --------- | ---- |
| Node appears, settles | A node is discovered (400 ms) |
| Edge flows | A pipeline component is building |
| Sweep | A pipeline component is under test |
| Loading line | The drill bar is waiting on a query |
| Panel slides in | The evidence panel opens (220 ms) |
| Tree eases | The tree grows towards the state the log describes, over about a second |
| Watering pulse | An allowed or escalated request: 1.1 s, and a new one only after the last |
| Hand-over | The tree fades to "Seeding complete" at the end of cleanup |

Under `prefers-reduced-motion`, every animation and transition is cut
to 0.01 ms and the tree draws its final state at once. At instant speed,
events arrive in bursts, so the tree settles without strobing (NFR-V7).

---

## 9. Contrast, tested

`backend/tests/test_design.py` reads `tokens.css` and checks, in both
themes, against WCAG 2.1 (NFR-V3):

- every text token on every surface, and on the selected-row tint, at
  4.5:1;
- the primary button's label on the accent, at 4.5:1;
- every chart role against the panel, at 3:1, except `muted`, which is
  meant to recede;
- every chart label on its fill, at 4.5:1: light text on a filled role,
  dark text on `baseline` and `muted`, as `charts/options.ts` chooses.

A new colour token, or a changed one, has to pass this test.
