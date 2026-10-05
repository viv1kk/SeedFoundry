# SeedFactory: Kickoff Prompt

Paste everything below the line into the first Claude Code session, run from the repo root.

---

You are starting a new project called **SeedFactory**: a lab that generates, tests and refines Seeds. Everything in it is simulated, deterministic and offline. There is no LLM connection and no real network call anywhere in the product.

## Read before you write anything

Read these in order. Do not skim the first five.

1. `docs/CLAUDE.md` (standing rules for every session)
2. `docs/README.md` (index and precedence rules)
3. `docs/project-notes.md` (what SeedFactory is and why)
4. `docs/requirements.md` (the binding spec)
5. `docs/ui-spec.md` and `docs/build-simulation.md` (screens, phases, logs, planted defects)
6. `docs/decisions.md`, `docs/implementation-plan.md`, `docs/methodology.md`
7. `docs/ensemble/ensemble_context.md` (what a Seed's four knowledge files mean)
8. `docs/seed_docs/README.md`, then every other file in `docs/seed_docs/`

`docs/seed_docs/` describes **Seed v0.1**, a finished prior project. It is reference material for patterns, conventions, data and visual language. It is not the spec for SeedFactory. Follow its own precedence rules and keep its two vocabularies (code terms vs screen terms) straight.

## Your task for this session: milestone M0 only

M0 is defined in `docs/implementation-plan.md`. In short:

1. Read everything above.
2. Write `docs/seed-reuse-notes.md`: for each item in requirements §9 ("What we take from Seed v0.1"), record where it lives in `docs/seed_docs/`, what exactly you will reuse (patterns, token values, data shapes, figures, shortcut keys, timing approach), and anything in the Seed docs that contradicts our docs.
3. Pin down the License Optimization dashboard from Seed v0.1: its panels, chart types, data fields and headline figures. Record them in `docs/seed-reuse-notes.md` §Dashboard. This becomes the polished iteration 2 dashboard and the baseline the iteration 1 defects are planted against.
4. Answer every item in `docs/decisions.md` §Open Questions that the Seed docs can settle, citing the file and section. Leave the rest open.
5. Scaffold the repo tree from `docs/implementation-plan.md` §Repo layout with empty packages, the toolchain from D-2, and a passing smoke test for backend and frontend. No features.
6. Add the M0 entry to the build log in `docs/project-notes.md` §Build log using the format in `docs/methodology.md`.

Then **stop**. Reply with: what you found, anything in our docs that is wrong or contradicted by the Seed docs, the open questions you could not close, and any change you would propose to the milestone plan. Do not start M1 until I confirm.

## Non-negotiables (also in docs/CLAUDE.md)

- Deterministic: the same intake files and the same actions produce the same event stream, logs, report and dashboard, every run.
- No LLM, no external API, no real network. "LLM calls" and "Seed API calls" are simulated behind interfaces so a real implementation could replace them later.
- The iteration 1 report must find its anomalies by actually checking the data, not by printing a hardcoded list.
- Iteration 2 is scripted (D-5): feedback text is stored and echoed, but does not change the outcome.
- Never edit a test assertion to make a test pass. If a test is wrong, record a decision first.
- No em dashes in any user-facing text or generated document.
