# SeedFactory: Operator guide

For whoever sets up the demo and presents it. Written 2026-10-04 for the build at M12, and checked against the build at M13 (the same day): every command, shortcut, label and time below is what the app does. The audience never sees the controls below: the demo controller is hidden until asked for (D-15).

---

## 1. Set up, once per machine

You need **Python 3.12 or newer** and **Node.js 22.18 or newer** on the path (the target machine has Node 24; the test runner and the rehearsal need 22.18). Both install per user, without admin rights. The first launch needs the network, to install packages. Nothing after that does (NFR-2, AC-9).

**On Windows**, where Windows Application Control may block uv, use `run.ps1` (D-25):

```
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

It makes `backend\.venv` with pip, installs the Python packages, installs the frontend's packages on the first run, and starts the app. Run the same command every time; it installs again only when `requirements.txt` changes. Add `-Dev` to install the test packages as well.

**Elsewhere, or where uv works:** `python run.py` (it makes `backend/.venv` with uv on the first run).

For the rehearsal (section 6) you also need **Google Chrome** (or Edge; set `CHROME` to its path if it is somewhere unusual).

---

## 2. Start and stop

```
python run.py
```

It prints `SeedFactory ready at http://127.0.0.1:5273/` once both processes answer. Open **that address**, as printed, in Chrome at 100% zoom, 1440 to 1920 px wide. `localhost` may resolve to an address Vite does not listen on.

`Ctrl+C` in the launcher's window stops both processes. On Windows, closing that window or ending the launcher in any other way also stops both (D-78). Elsewhere, use Ctrl+C: see section 8.

The launcher refuses to start if something already answers on port 8100 or 5273: stop the earlier server first (section 8).

Every browser tab on the app shares one lab. Close other tabs on it before presenting, or a click there changes what is on screen.

Knowledge, builds and the approval are kept in `var/state.json` and survive a restart. **Reset to start** (Shift+R) clears them.

---

## 3. Controls

All shortcuts are on **Shift**, and none fires while the caret is in a text field (the Knowledge editor, a name field, the rebuild modal's text), so typing a capital letter is always safe (D-47). Digits match the key's position, so Shift+1, Shift+2 and Shift+4 work on any keyboard layout.

| Keys | Does |
|---|---|
| **Shift+O** | Show or hide the demo controller (bottom right) |
| **Shift+P** | Load sample Seed: the four License Optimization initiation files (Identity.md, Tools_and_Skills.md, Environment_01.md, Value_0001.md). Asks first if Knowledge has files |
| **Shift+Enter** | Start Build, once the four initiation files are in; opens the Build page |
| **Shift+1** / **Shift+2** / **Shift+4** | Build speed 1x (the presentation pace), 2x, 4x |
| **Shift+S** | Skip to the end of the current phase |
| **Shift+E** | Skip to the end of the build |
| **Shift+F** | Prefill the rebuild feedback with the demo text, when the rebuild modal is open (not with the caret in its text) |
| **Shift+C** | Clear Knowledge (asks first) |
| **Shift+R** | Reset to start: no files, no builds, no approval (asks first) |
| **Shift+D** | Switch between the light and dark themes |

The **demo controller** (Shift+O) has a button for every shortcut and a status line that says what the last action did, or why it could not run. Escape or Shift+O closes it.

Speed and skip change only the pacing, never what a build does or says (FR-DC-4); they act within a twentieth of a second. Speed survives Reset.

There is no shortcut for **Reject** or **Approve**: press them on the report, where the audience sees them. Every report has both, whatever its verdict (D-81).

---

## 4. Giving the demo

The narrative runs **8 to 10 minutes at 1x**. The two builds take 75 seconds each (the 1x rehearsals on 2026-10-04 measured 75.5 s and 75.7 s by the wall clock in M12, and 75.5 s for both in M13); the rest is your pace. Times below are from the start, at a steady pace with little talk; slow down where the audience is interested.

| When | On screen | What you do |
|---|---|---|
| Before | Knowledge, empty: the four Ensemble files explained, one line each | Reset (Shift+R) if anything is there. Speed 1x (Shift+1). Hide the controller |
| 0:00 | Knowledge | Say what a Seed is built from. Press **Shift+P**: the four initiation files load, the Initiation files checklist turns complete (each with the Seed file it maps to, muted, on the right), Start Build lights up. Open `Value_0001.md`, switch to **Preview**: purpose, principles, value logic, decision logic. Point out the mic (voice input, shown only) |
| 1:30 | Knowledge | **Start Build** (or Shift+Enter). The Build page opens |
| 1:30 to 2:45 | Build, iteration 1: the stepper on the left, the console on the right | Narrate as phases pass: Assay counts sections and runs the boundary check; Distillation and Synthesis write `core.md`, `adaptation.md`, `protection.md`; Containment uploads them to a sandbox; Planting and Seeding & Life run the simulated Seed v0.1, its three human gates auto-resolved from the knowledge files; Stress & Probe and Harvest Validation find problems (amber, then red FAIL lines). Use the console's filter to show only FAIL |
| 2:45 | The **Build Report**: Completed with findings, 14 findings | Walk the groups: Numeric (high), Visual, Latency; each with expected and shown. "Every one of these was recomputed from the data, not typed in" |
| 3:30 | **View Agentic Solution**: iteration 1, plainly unfinished | Let it sink in: mixed number formats, a twelve-slice pie, a red line, a serif title, the treemap waiting 4.5 s. Back to report, then click **N-1**: the dashboard opens with the panel outlined and the finding named |
| 4:30 | Back to report, **Reject** | The modal: switch to **Feedback + Dashboard** to write while looking at it. Click a tab (not the text) and press **Shift+F** to prefill. Read a line or two of the feedback |
| 5:00 | **Start Rebuild**: Build, iteration 2 | Phase 1 opens with **Apply observer feedback**, and the **Observer feedback into Knowledge** panel above the stepper shows each segment going into Identity.md, Tools_and_Skills.md, Environment_01.md and Value_0001.md as the console says where it went; each file is updated, and Environment_01.md and Value_0001.md step to Environment_02.md and Value_0002.md, their next versions (open Knowledge in passing if you want to show the new names and the "Observer feedback (iteration 1)" sections; it is read-only while the build runs). Point out the Human tag beside "Iteration 2": this iteration exists because a person rejected the last one |
| 6:15 | Iteration 2's report: **Passed**, 0 findings | **Changes since iteration 1**: 14 of 14 resolved, the feedback quoted, the files it updated. **Context footprint when planted**: the three Seed files take 15.8% of the context window, under the 20% budget. Point out that iteration 2 also has **Reject**: the loop goes on until the observer approves. **Initiate QUAD SI Review Protocol** beside Approve is shown only: it does nothing |
| 6:45 | **View Agentic Solution**: iteration 2, polished | Drill: click a treemap cell, then a product, a class, down to the seats; the breadcrumb and Back step out again |
| 7:45 | Back to report, **Approve** | The Seed page: the Seed's name, Approved, the date; what it does; the tests by phase; the iteration history (open **Show the feedback**); the three files |
| 8:30 | The Seed files | **Preview** `protection.md` and scroll to **Learned rules**: one rule per class of finding, learned from iteration 1. **Secure and Lock in Secure Repository** is shown only; the **download** link beside it saves the zip |
| 9:00 | End | Optional: before Approve, **Reject** iteration 2 instead, Shift+F (refinements), Start Rebuild: iteration 3 runs the 11 phases again, the panel shows the new feedback going into the four files, and the report reads Passed with "Changes since iteration 2"; then Approve it. Optional second ending: Reset, Shift+P, Shift+4, Start Build, and **Approve iteration 1** instead: the Seed page lists the 14 open findings as known issues, and so does each file |

---

## 5. If something goes wrong on stage

- **A build seems slow:** Shift+2 or Shift+4 speeds it up; Shift+S finishes the current phase. Nothing it shows changes.
- **Shift+F types an F:** the caret is in the feedback text. Click a view tab, then press it again.
- **Start Build says the Seed is approved:** it was approved earlier. Reset (Shift+R).
- **The page looks stale after a server restart:** reload the browser tab; a build that was running when the server stopped is marked as stopped, and Start Build runs it again from Knowledge.

---

## 6. Rehearsing

**The automated rehearsal** runs the whole demo in a hidden Chrome, against its own copy of the app on spare ports with a throwaway `var/`, so the app you present and its state are never touched:

```
cd frontend
npm run rehearse -- --speed 4          (about 2.5 minutes)
npm run rehearse                       (1x, timed, about 3.5 minutes)
npm run rehearse -- --out ..\rehearsal (keep the screenshots somewhere you choose)
```

It cuts the network off (Chrome resolves no host but this machine; the backend runs under a guard that refuses any connection outside it), then plays the demo through the UI with the shortcuts above, and checks: Start Build gating, the shortcuts and the text-field rule, a reload mid-build, the 14 findings, both dashboards rendering in under a second, the rebuild with Prefill, iteration 2 passing with 14 of 14 resolved, Approve and the downloads, a server restart, Reset, the iteration 1 approval with its known issues, every control reachable by Tab with a visible focus ring, typing in a 1 MB file, and that nothing was requested outside 127.0.0.1. It prints one line per check, saves screenshots of every page in both themes and a `results.json`, and exits non-zero if anything failed. Close the presenting app first only if your machine is short of memory; the two do not interfere.

**By hand:** 4x and skip run the narrative quickly; Reset puts everything back. The dashboard opens directly at `http://127.0.0.1:5273/review/1?dashboard=license-optimization` once iteration 1 has built.

---

## 7. Checks before a demo

1. `python run.py test` (or `powershell -ExecutionPolicy Bypass -File .\run.ps1 -Dev test`): the backend and frontend suites should both report pass. Run it with nothing else heavy running, the rehearsal included: on a loaded machine a slow frontend test can time out (R-10). If one does, run it again alone; a test that fails alone is a real fault.
2. `npm run rehearse -- --speed 4` from `frontend/`: every check should pass.
3. To be sure it is offline: turn the machine's network off, launch, and run through to the Seed page. Nothing changes.
4. Launch with `python run.py`, open the printed address in Chrome, set the zoom to 100%, choose the theme (Shift+D; a first visit is dark, the ValueWise presentation default, and light is for bright rooms), and close every other tab on the app.
5. Reset (Shift+R), speed 1x (Shift+1), demo controller hidden.

---

## 8. Troubleshooting

| Symptom | Cause, and what to do |
|---|---|
| "Something already answers at http://127.0.0.1:8100" (or 5273) | An earlier server is still running. Stop it (close its window, or end its process tree), check nothing listens on 8100 or 5273, and launch again |
| The app behaves like an older version | A stale server on the port from before an update. Stop everything and launch again |
| Not on Windows: the ports stay taken after the launcher was ended from outside | Only Ctrl+C stops both processes there. End the uvicorn and Vite processes (they hold 8100 and 5273), then launch again. On Windows the launcher's children end with it (D-78) |
| `uv` or the venv's `python.exe` is blocked by Windows | Application Control. Use `run.ps1` (section 1) |
| `localhost:5273` does not load | Use the printed address, `http://127.0.0.1:5273/` |
| The treemap shows a spinner for 4.5 s on iteration 1 | Planted (L-1). Every other panel draws at once |
| Start Build is refused: "This Seed is approved" | Reset to start (Shift+R) |
| A build reads "This build stopped before it finished" | The server stopped mid-build. Start Build again from Knowledge |
| The rehearsal says "No Chrome found" | Set `CHROME` to Chrome's or Edge's `.exe` and run it again |
| The rehearsal fails a check | Its line says what it saw; the screenshots in the out folder show the page. `stopped-here.png` is the page where it stopped |

---

*Change request CR-2 (2026-10-05):* the product is SeedFactory (D-87). Knowledge offers the four initiation files only (D-84); the console's small note under its bar about English is always there (D-89). The rehearsal (section 6) checks these and passes 34 of 34, including that the Build page never scrolls the window away (D-95).
