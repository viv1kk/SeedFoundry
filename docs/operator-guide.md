# SeedFactory: Operator guide

For whoever sets up the demo and presents it. Written 2026-10-04 for the build at M12, and checked against the build at M13 (the same day): every command, shortcut, label and time below is what the app does. The audience never sees the controls below: the demo controller is hidden until asked for (D-15).

---

## 1. Set up, once per machine

*Rewritten 2026-10-12 (D-108): on Windows, `run.ps1` now installs everything itself.*

The set-up needs the network once, to download Python, Node.js and the packages. After that nothing does: the app runs offline (NFR-2, AC-9). Nothing needs admin rights.

**Get the code.** Clone the repository (or unzip a copy) and open a terminal in its folder:

```
git clone https://github.com/viv1kk/SeedFoundry.git
cd SeedFoundry
```

### Windows: one command

```
powershell -ExecutionPolicy Bypass -File .\run.ps1 setup
```

It assumes nothing is installed and skips each step that is already done, so it is safe to run again at any time:

1. **Python 3.12 or newer**, for this user: with winget, else the python.org installer (3.12.10). A Python already on the machine is used if it is 3.12 or newer, including one that uv manages. The Microsoft Store's Python is passed over (section 8).
2. **Node.js 22.18 or newer**: the current LTS zip from nodejs.org, checked against nodejs.org's checksums, unpacked to `%LOCALAPPDATA%\Programs\nodejs` and put first on your user PATH. A Node.js already on the machine is used if it is new enough.
3. **`backend\.venv`**, the backend's Python environment, made with pip. A venv that does not work, or was made from the Store's Python, is made again.
4. **The Python packages**, pinned in `backend\requirements-dev.txt` (the app's and the tests'). They install again only when that file changes.
5. **The frontend packages**, with `npm ci` from `frontend\package-lock.json`. They install again only when the lock file changes.
6. **Chrome or Edge**: only reported, as only the rehearsal (section 6) needs one.

It ends with "SeedFactory is set up". The first run takes a few minutes; a run with nothing to do takes seconds. `-ExecutionPolicy Bypass` applies to this one command only and changes no setting.

Then:

| Command | What it does |
|---|---|
| `powershell -ExecutionPolicy Bypass -File .\run.ps1` | Sets up anything missing, then starts the app (section 2) |
| `powershell -ExecutionPolicy Bypass -File .\run.ps1 test` | Sets up with the test packages, then runs both test suites |
| `powershell -ExecutionPolicy Bypass -File .\run.ps1 setup` | Sets up, then stops |

After pulling a new version, run the same command: changed packages install, everything else is skipped. A new terminal window sees the Node.js that the set-up installed; the window the set-up ran in already does.

### macOS and Linux, or Windows by hand

Install **Python 3.12 or newer** and **Node.js 22.18 or newer** yourself, then from the repository folder:

```
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
cd frontend && npm ci && cd ..
python3 run.py
```

On Windows by hand the venv's Python is `backend\.venv\Scripts\python.exe`, and the Microsoft Store's Python should not be used (section 8). Where uv works, `uv sync --project backend` replaces the first two lines, and `python run.py` runs it by itself on the first launch if `backend/.venv` is missing (D-25). After changing the backend's dependencies, re-export the pip files as `CLAUDE.md` says.

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

It cuts the network off (Chrome resolves no host but this machine; the backend runs under a guard that refuses any connection outside it), then plays the demo through the UI with the shortcuts above, and checks: Start Build gating, the shortcuts and the text-field rule, a reload mid-build, the 14 findings, both dashboards rendering in under a second, the rebuild with Prefill, iteration 2 passing with 14 of 14 resolved, Approve and the downloads, a server restart, Reset, the iteration 1 approval with its known issues, every control reachable by Tab with a visible focus ring, typing in a 1 MB file, and that nothing was requested outside 127.0.0.1. It prints one line per check, saves screenshots of every page in both themes, each chart hovered in both themes (`06-hover-*.png`), and a `results.json`, and exits non-zero if anything failed. Close the presenting app first only if your machine is short of memory; the two do not interfere.

**By hand:** 4x and skip run the narrative quickly; Reset puts everything back. The dashboard opens directly at `http://127.0.0.1:5273/review/1?dashboard=license-optimization` once iteration 1 has built.

---

## 7. Checks before a demo

1. `python run.py test` (or `powershell -ExecutionPolicy Bypass -File .\run.ps1 test`): the backend and frontend suites should both report pass. Run it with nothing else heavy running, the rehearsal included: on a loaded machine a slow frontend test can time out (R-10). If one does, run it again alone; a test that fails alone is a real fault.
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
| `run.ps1` says "Set-up stopped: could not download ..." | The set-up needs the network once. Connect, or set a proxy that PowerShell can use, and run it again; it carries on from where it stopped |
| `run.ps1` installs a Python although one is installed | The one installed is older than 3.12, or is the Microsoft Store's. The Store's Python runs in a package container whose child processes escape the launcher's job object, so a launcher ended from outside would leave uvicorn and Vite running (D-78, D-108). The set-up installs the python.org one for your user instead |
| `run.ps1` says Node.js is "still not first on the PATH" | An older Node.js installed for all users comes first on the PATH. Uninstall it, or move `%LOCALAPPDATA%\Programs\nodejs` before it, and run the set-up again |
| `node` or `npm` is not found in a window opened before the set-up | That window has the old PATH. Open a new one |
| A frontend test finds Windows line ends (`\r\n`) in a fixture | A checkout from before `.gitattributes` (D-108). Delete the `.md` files in `frontend/tests/fixtures`, then run `git checkout -- frontend/tests/fixtures` |
| `localhost:5273` does not load | Use the printed address, `http://127.0.0.1:5273/` |
| The treemap shows a spinner for 4.5 s on iteration 1 | Planted (L-1). Every other panel draws at once |
| Start Build is refused: "This Seed is approved" | Reset to start (Shift+R) |
| A build reads "This build stopped before it finished" | The server stopped mid-build. Start Build again from Knowledge |
| The rehearsal says "No Chrome found" | Set `CHROME` to Chrome's or Edge's `.exe` and run it again |
| The rehearsal fails a check | Its line says what it saw; the screenshots in the out folder show the page. `stopped-here.png` is the page where it stopped |

---

*Change request CR-2 (2026-10-05):* the product is SeedFactory (D-87). Knowledge offers the four initiation files only (D-84); the console's small note under its bar about English is always there (D-89). The rehearsal (section 6) checks these and passes 34 of 34, including that the Build page never scrolls the window away (D-95).
