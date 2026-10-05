# SeedFactory: Methodology

How work on SeedFactory is planned, done, checked and recorded. Adapted from Seed v0.1's process (requirements, decision record, milestone plan, build log, amendments).

## 1. Principles

1. **Docs lead, code decides.** Requirements and decisions are written before code. Once code exists, it is the truth and docs are corrected to match it.
2. **One milestone at a time.** Each milestone has scope, exit criteria and hand checks. Finish, log, stop, report.
3. **Amend, never erase.** Changed requirements become amendments (A-n) with the old text struck through. Superseded decisions stay visible.
4. **Tests are a contract.** Assertions are not edited to make tests pass. A wrong assertion needs a decision entry first.
5. **Simulate honestly.** Do real work where it is cheap (lint, stats, validators, generation); simulate only what would need an LLM or a live Seed. Label simulated figures as simulated.
6. **Ensemble discipline applies to us too.** When writing the sample Seed or templates, keep each concern in its one home per `ensemble/ensemble_context.md` §6.

## 2. The cycle for each milestone

1. **Orient:** read the milestone in `implementation-plan.md`, the requirements it covers, and the related decisions. Re-read `seed-reuse-notes.md` if reusing anything.
2. **Plan:** list the files to add or change (tag NEW, CHANGE, MOVE) and the tests that prove the exit criteria. If a product question appears, add it to `decisions.md` §Open questions and ask before building on a guess.
3. **Build:** tests first where the behaviour is crisp (validators, rules, persistence, determinism); alongside the code elsewhere.
4. **Gate:** run all suites; run determinism and no-em-dash tests; check no assertion was edited without a decision.
5. **Hand check:** do the milestone's hand checks in a browser.
6. **Record:** build log entry, milestone status, doc corrections.
7. **Report and stop:** summarise for the stakeholder: what changed, what to look at, open questions, proposed next step.

## 3. Ids and where they live

| Prefix | Meaning | File |
|---|---|---|
| G-n | Goal | requirements.md |
| FR-xx-n | Functional requirement | requirements.md |
| NFR-n | Non-functional requirement | requirements.md |
| AC-n | Acceptance criterion | requirements.md |
| A-n | Requirement amendment | requirements.md |
| D-n | Decision | decisions.md |
| OQ-n | Open question | decisions.md |
| R-n | Risk | decisions.md |
| M-n | Milestone | implementation-plan.md |
| T-nn | Build test (inside the simulated build) | build-simulation.md |
| N-n, V-n, L-n, B-xxx | Findings: numeric, visual, latency, boundary | build-simulation.md |

*As built (M13):* a boundary advisory's id is its rule and a count, such as `B-DATA-1` (D-50); a problem no catalogue entry owns becomes `N-X1`, `V-X1` or `L-X1` (D-63). Protection rules derived from the intake are `P-n` and the fixed probes `PB-1` to `PB-10` (D-62). Builds are `b-n` and files `f-n`, from saved counters (D-32, D-49).

## 4. Build log entry format

Add to `project-notes.md` §Build log at the end of each milestone. Modelled on Seed v0.1's `project-notes.md` §84.5.

```
### M<n>: <title> (YYYY-MM-DD)

**What changed**
- Two to six bullets in plain language, user-visible first.

**Files**
- NEW backend/seedfoundry/engine/clock.py
- CHANGE frontend/src/views/Build.vue
- MOVE ...

**Gates**
- backend: <n> passed, frontend: <n> passed
- determinism: pass | no-em-dash: pass | network: pass
- assertions edited: none (or: D-<n>)

**Hand checks**
- <what was checked in the browser and the result>

**Decisions and questions**
- New: D-<n> ...
- Opened: OQ-<n> ...
- Closed: OQ-<n> (answer, source)

**Notes for next milestone**
- Anything the next session must know.
```

## 5. Commits

- One logical change per commit; message starts with the milestone (`M3: import dialog with category pre-selection`).
- Docs changes that record decisions go in the same commit as the code they explain.

## 6. When to stop and ask

Stop and ask the stakeholder when:
- A requirement is ambiguous and the answer changes what the user sees.
- The Seed docs contradict our docs on something user-visible.
- A milestone's exit criteria cannot be met without changing scope.
- A test assertion appears wrong.

Do not stop for purely technical choices that satisfy the NFRs: decide, record a D-n, move on.
