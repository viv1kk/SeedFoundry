# Seed v0.1 --- Operator guide

> **For** whoever sets up the demo and presents it. Written 2026-10-02
> for the build at M22. The audience never sees the controls below
> (FR-O2): there is no transport bar, and the operator panel is hidden
> until asked for.

---

## 1. Set up, once per machine

You need **Python 3.12 or newer** and **Node.js 20 or newer** on the
path. Both can be installed per user, without admin rights. The first
launch needs the network, to install packages. Nothing after that does
(NFR-D2).

**On Windows**, use `run.ps1`. It works where Windows Application
Control blocks uv (D-21):

```
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

It creates `.venv`, installs the Python packages, installs the
frontend's packages on the first run, and starts the app. Run the same
command every time; it installs again only when `requirements.txt`
changes. Add `-Dev` to install the test dependencies as well.

**Elsewhere, with uv:** `uv run run.py`.

**Elsewhere, with pip:**

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

---

## 2. Start and stop

The launcher prints `Seed v0.1 ready at http://localhost:5173` once both
servers answer. Open that address in a desktop browser at presentation
resolution; 1600 × 1000 or larger reads best (NFR-L4). Use `localhost`:
the frontend does not answer on `127.0.0.1:5173`.

`Ctrl+C` in the launcher's window stops both servers.

Every browser connected to the app shares one run. Close other tabs on
it before presenting, or a click there changes the run on screen.

---

## 3. Controls

All shortcuts are on **Shift**, and none fires while the cursor is in a
text field, so typing a capital letter into the credential form is safe
(M22).

| Keys | Does |
| ---- | ---- |
| **Shift+O** | Show or hide the operator panel |
| **Shift+P** | Load the bundled seed files into the three slots (FR-S7) |
| **Shift+Enter** | Plant the seed, on the seed screen; start the run, once planted |
| **Shift+1** | Speed 1x, the presentation pace |
| **Shift+2** | Speed 2x |
| **Shift+0** | Instant: no delays at all |
| **Shift+S** | Skip to the end of the current phase |
| **Shift+R** | Reset: clear the run and return to the seed screen |
| **Shift+D** | Switch between the light and dark themes |

The shortcuts read the character typed, so Shift+1, Shift+2 and Shift+0
assume a US-style layout, where they type `!`, `@` and `)`. On another
layout, use the operator panel's speed buttons.

The **operator panel** (Shift+O) shows the lifecycle state, the run
status, the stream's connection, the event count and any gaps. It has
buttons for every shortcut, plus two rehearsal tools: **Evidence**, to
revise a profiled field's completeness (section 6), and **Rehearse a
dashboard**, to open any dashboard without a run.

Speed and skip take effect within a twentieth of a second, and change
nothing but timing (FR-O3). Speed survives a Reset.

---

## 4. Giving the demo

The narrative is timed at **270 seconds at 1x**, plus the time spent
answering. A 1x rehearsal at M22 took 268 s; the moments below are from
that run.

| When | On screen | What you do |
| ---- | --------- | ----------- |
| Before | The seed screen: three layer cards, Core, Adaptation, Protection | Drop `core.md`, `adaptation.md` and `protection.md` from `seeds/` onto their cards, or press Shift+P. Each card shows its parsed headings. Then **Initialize**, or Shift+Enter |
| 0 s | The workspace in Both: the Planting stage with the declared stack on the left, the seed in the soil on the right | Shift+Enter starts the run |
| ~30 s | **Authentication required**: ServiceNow's Incident API | Type an account and a secret, anything at all, and **Configure**. The values are used once and discarded |
| to ~200 s | Discovery builds the environment graph, one timeout recovers, and assessment grades the three methodologies: HIGH, PARTIAL and MEDIUM, with one routing problem | Point out the DENY in the stream (PR-033), and the Protection tab's counts |
| ~200 s | **Approval required**: 3 of 3 Agent Components | Approve each on its card, or open **Review** for the evidence first. Scroll the stage if the buttons are below the fold |
| to ~258 s | Implementation builds Agent One VW: three pipelines, their tests, the tree growing a branch for each | --- |
| ~258 s | **Confirmation required** | Press **Run — clean up and close seeding** |
| ~273 s | Cleanup: four steps, each with its rule. The tree sheds its stake and seed. The screen hands over to Life | --- |
| +45 s | Life collects twelve simulated weeks and recalibrates three times, then reads "Caught up" | Press **Run** on Ticket Anomaly Detection while it is collecting. The totals grow with each week |
| After | The Ticket Intelligence dashboard | Click into the treemap, a cluster, then a ticket. The view pins ("Pinned to week N · K newer collections"); **Catch up** moves it on. Open **Evidence**. **← Agent Components** returns to the list |

The **Growth** control in the Life pane's header drops the grown tree
open again at any point after the hand-over.

A pending request always brings the Seeding pane into view. Otherwise
the layout follows the run, and the control in the top bar overrides it
until the run next changes it.

---

## 5. Rehearsing

- **Instant speed** (Shift+0) runs the narrative in seconds. It still
  stops for every request.
- **Skip** (Shift+S) finishes the current phase at once. In Life, it
  completes collection.
- **Open a dashboard directly.** The operator panel's **Rehearse a
  dashboard**, or a link:

  ```
  http://localhost:5173/?dashboard=ticket-anomaly-detection
  http://localhost:5173/?dashboard=license-optimization
  http://localhost:5173/?dashboard=application-portfolio-rationalization
  ```

  A link may carry a drill path (`&drill=...`) and a collection step
  (`&step=4`), exactly as the address bar shows them during a run. The
  browser's Back pops one drill step.

---

## 6. Showing that the grades are computed

In the operator panel, under **Evidence**, choose a profiled field, set
its completeness, and press **Revise completeness**. Every assessment
that rests on the field is regraded through the same computation, and
the stream records the revision. For example, raising
`sap.contract_item.unit_price` from 64% to 95% moves License
Optimization from PARTIAL to HIGH, as `test_assessment.py` asserts. Set
it back to 64 to restore the narrative's grade. This is M7's proof that Potential is computed, not authored
(FR-A2).

---

## 7. Checks before a demo

With `run.ps1 -Dev` run once:

```
.venv\Scripts\python.exe -m pytest -q
```

It should report 561 passed. One timing test may fail on a heavily
loaded machine; that is known and harmless. For the frontend, from
`frontend/`: `npm run typecheck` and `npm run build`.

---

## 8. Troubleshooting

| Symptom | Cause, and what to do |
| ------- | --------------------- |
| The launcher says the port is in use, or the app behaves like an older version | An earlier server is still running on port 8000 or 5173. Stop it (close its window, or end its process tree), confirm nothing listens on those ports, and launch again |
| `uv` or the venv's `python.exe` is blocked by Windows | Application Control. Use `run.ps1` (section 1) |
| `run.ps1` says the packages installed but will not import | Smart App Control is blocking pandas's compiled files for that Python version. Install another Python version, delete `.venv`, and run `run.ps1` again |
| `127.0.0.1:5173` does not load | Use `http://localhost:5173` |
| The tree pulses blue once after a page reload | Expected (A-16). The tree itself is unchanged |
| The page is slow while the tree grows or a dashboard follows collection | Each redraws often. On a slower machine, present at 1x rather than 2x, and open dashboards once Life is caught up |
