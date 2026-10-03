"""A build's script: every beat of every phase, with its events and simulated time
(build-simulation.md §1 to §4).

Each sub-step is a generator that yields beats and returns a one-line summary. A beat
is a relative weight and the events it emits; a phase's beats share the phase's time
(its weight x 0.75 s) in proportion to their weights, so `sim_t` comes from the
schedule and never from a clock. The script is a pure function of the intake, the
iteration and the earlier build, made in full when the build starts: speed and skip,
which the runner applies, cannot change a word of it (FR-DC-4, NFR-1).

Real work happens here where it is cheap (Assay statistics, the boundary check, the
manifest and its checksums, the gates' citations). LLM and Seed API calls go through
the simulated clients (D-22). The validators of phases 9 and 10 report "not run" until
M9 (D-51). T-08 runs the dashboard's logic on both datasets of M7 (D-58).
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from collections.abc import Callable, Generator
from dataclasses import dataclass, field
from typing import Any

from seedfoundry import dashboard
from seedfoundry.clients import ApiCall, LLMCall, LLMClient, SeedClient, SimulatedLLMClient, SimulatedSeedClient
from seedfoundry.data import DATASETS, dataset
from seedfoundry.engine.catalogue import BUDGET_SECONDS, PHASES, TEST_NAMES, TOTAL_WEIGHT, Phase, plan
from seedfoundry.generate import outline as layers
from seedfoundry.intake import assay, boundary
from seedfoundry.intake.feedback import FEEDBACK_NAME, feedback_file, segments
from seedfoundry.state import Build, Category, IntakeFile
from seedfoundry.validators import structure

GATES = ("servicenow-incident-api", "solution-approval", "close-seeding")

# Default weights of a beat, relative to the others in its phase.
LOG, LLM, API, TEST = 1.0, 3.0, 1.5, 1.0


@dataclass
class Beat:
    weight: float
    events: list[dict[str, Any]]
    phase_index: int = 0
    sim_t: float = 0.0


def event(type: str, message: str, level: str = "INFO", code: str | None = None, **data: Any) -> dict[str, Any]:
    return {"type": type, "level": level, "message": message, "code": code, "data": data}


def plural(count: int, word: str, many: str | None = None) -> str:
    return f"{count:,} {word if count == 1 else many or word + 's'}"


def rng_for(digest: str, iteration: int) -> random.Random:
    """The build's RNG: sha256 of the intake content plus the iteration (build-simulation.md §1)."""
    return random.Random(int(hashlib.sha256(f"{digest}:{iteration}".encode()).hexdigest(), 16))


@dataclass
class BuildContext:
    """What a build reads, and what its steps record for the steps after them."""

    build_id: str
    iteration: int
    files: list[IntakeFile]
    prior: Build | None = None  # iteration 1's build, for iteration 2
    llm: LLMClient | None = None
    seed: SeedClient | None = None

    results: dict[str, str] = field(default_factory=dict)  # test id: pass, warn, fail or not_run
    findings: list[dict[str, Any]] = field(default_factory=list)
    gates: list[str] = field(default_factory=list)
    drafts: dict[str, str] = field(default_factory=dict)
    manifest: dict[str, Any] = field(default_factory=dict)
    uploads: dict[str, str] = field(default_factory=dict)  # name: sha256 the Seed API returned
    seed_id: str = ""
    sandbox_id: str = ""

    def __post_init__(self) -> None:
        self.files = [f.model_copy() for f in self.files]
        self.digest = assay.digest(self.files)
        self.fingerprint = self.digest[:6]
        self.rng = rng_for(self.digest, self.iteration)
        self.llm = self.llm or SimulatedLLMClient(self.rng)
        self.seed = self.seed or SimulatedSeedClient(self.rng)
        self.inventory = assay.inventory(self.files)
        self.core = {f.category: f for f in self.inventory.core}
        self.seed_name = assay.seed_name(self.core.get(Category.MUSIC))

    def name(self, category: Category) -> str:
        found = self.core.get(category)
        return found.name if found else assay.CATEGORY_LABELS[category]

    def text(self, *categories: Category) -> str:
        return "\n".join(self.core[c].content for c in categories if c in self.core)

    def record(self) -> Build:
        return Build(
            id=self.build_id,
            iteration=self.iteration,
            seed_name=self.seed_name,
            fingerprint=self.fingerprint,
            plan=plan(self.iteration),
            sim_seconds=BUDGET_SECONDS,
        )


Step = Generator[Beat, None, str | None]


# Beat helpers


def log(message: str, level: str = "INFO", weight: float = LOG, **data: Any) -> Beat:
    return Beat(weight, [event("log", message, level, **data)])


def llm(call: LLMCall, weight: float = LLM) -> Beat:
    return Beat(weight, [event("llm.call", call.message, "LLM", **call.as_data())])


def api(call: ApiCall, weight: float = API) -> Beat:
    return Beat(weight, [event("api.call", call.message, "API", **call.as_data())])


TEST_LEVELS = {"pass": "PASS", "warn": "WARN", "fail": "FAIL", "not_run": "TEST"}


def test(ctx: BuildContext, test_id: str, status: str, detail: str, *, simulated: bool = False, arrives_in: str | None = None) -> Beat:
    ctx.results[test_id] = status
    data: dict[str, Any] = {"id": test_id, "name": TEST_NAMES[test_id], "status": status, "detail": detail, "simulated": simulated}
    if arrives_in:
        data["arrives_in"] = arrives_in
    return Beat(TEST, [event("test.result", f"{test_id} {TEST_NAMES[test_id]}: {detail}", TEST_LEVELS[status], test_id, **data)])


def not_run(ctx: BuildContext, test_id: str, what: str, milestone: str) -> Beat:
    return test(ctx, test_id, "not_run", f"not run, {what} arrives in {milestone}", arrives_in=milestone)


# Phase 1: Assay


def feedback_route(ctx: BuildContext) -> Step:
    feedback = feedback_file(ctx.files)
    if feedback is None:
        yield log(f"No {FEEDBACK_NAME} in Knowledge, so there is no observer feedback to route")
        return "nothing to route"
    parts = segments(feedback.content)
    yield log(
        f"Read {FEEDBACK_NAME}: {plural(len(parts), 'segment')}, {feedback.size:,} bytes",
        segments=len(parts),
        bytes=feedback.size,
    )
    yield log("Routing feedback to the Ensemble files arrives in M10, so no segment was routed", routed=0)
    return "not routed (arrives in M10)"


def feedback_update(category: Category, last: bool = False) -> Callable[[BuildContext], Step]:
    def step(ctx: BuildContext) -> Step:
        yield log(f"{ctx.name(category)}: no change, no feedback was routed to it", lines_added=0)
        if last:
            yield log(f"Intake unchanged: 0 files changed, fingerprint {ctx.fingerprint}", files_changed=0, fingerprint=ctx.fingerprint)
        return "no change"

    return step


def inventory(ctx: BuildContext) -> Step:
    inv = ctx.inventory
    yield log(
        f"Inventory: {plural(len(inv.core), 'core file')}, {plural(len(inv.context), 'context file')}, {assay.kilobytes(inv.total_bytes)}",
        files=[f.summary() for f in inv.core + inv.context],
        bytes=inv.total_bytes,
    )
    if inv.missing:
        yield test(ctx, "T-01", "fail", f"missing {assay.missing_labels(inv.missing)}")
    else:
        yield test(ctx, "T-01", "pass", "4 of 4 present, each with content")
    return f"{len(inv.core) + len(inv.context)} files"


def coverage(ctx: BuildContext) -> Step:
    found = expected = 0
    gaps: list[str] = []
    for file in ctx.inventory.core:
        result = assay.coverage(file)
        found += len(result.found)
        expected += len(result.expected)
        missing = f", missing {', '.join(result.missing)}" if result.missing else ""
        if result.missing:
            gaps.append(file.name)
        yield log(
            f"{file.name}: {len(result.found)} of {len(result.expected)} Ensemble sections ({result.percent}%){missing}",
            file=file.name,
            found=result.found,
            missing=result.missing,
            percent=result.percent,
        )
    if gaps:
        yield test(ctx, "T-02", "warn", f"{found} of {expected} sections; gaps in {', '.join(gaps)}")
    else:
        yield test(ctx, "T-02", "pass", f"{found} of {expected} sections across {plural(len(ctx.inventory.core), 'file')} (100%)")
    return f"{found} of {expected} sections"


def boundary_check(ctx: BuildContext) -> Step:
    yield log(f"Boundary check: {len(boundary.RULES)} rules over {plural(len(ctx.inventory.core), 'core file')}")
    counts: dict[str, int] = {}
    advisories = boundary.lint(ctx.inventory.core)
    for advisory in advisories:
        counts[advisory.rule] = counts.get(advisory.rule, 0) + 1
        finding_id = f"{advisory.rule}-{counts[advisory.rule]}"
        finding = {
            "id": finding_id,
            "category": "Boundary",
            "advisory": True,
            "severity": "advisory",
            "phase": "assay",
            "file": advisory.file,
            "expected": f"in {advisory.home}",
            "shown": advisory.excerpt,
            **advisory.as_data(),
        }
        ctx.findings.append(finding)
        yield Beat(
            0.5,
            [
                event(
                    "finding.raised",
                    f'{finding_id} {advisory.file} line {advisory.line}: "{advisory.match}" belongs in {advisory.home} (advisory)',
                    "WARN",
                    finding_id,
                    **finding,
                )
            ],
        )
    if advisories:
        yield test(ctx, "T-03", "warn", f"{plural(len(advisories), 'advisory', 'advisories')}, reported and not counted against the verdict")
    else:
        yield test(ctx, "T-03", "pass", "0 findings")
    return plural(len(advisories), "advisory", "advisories")


def fingerprint(ctx: BuildContext) -> Step:
    count = len(ctx.inventory.core) + len(ctx.inventory.context)
    yield log(f"Intake fingerprint {ctx.fingerprint} (sha256 over {plural(count, 'file')})", fingerprint=ctx.fingerprint, sha256=ctx.digest)
    return ctx.fingerprint


# Phase 2: Distillation


def profile(ctx: BuildContext) -> Step:
    file = ctx.core[Category.INSTRUMENT_AWARENESS]
    parts = assay.sections(file.content)
    title = parts[0].title if parts else file.name
    described = title.split(":", 1)[1].strip() if ":" in title else title
    yield log(f"Model profile from {file.name}: {described}", profile=described)
    found = assay.coverage(file).found
    yield log(f"Profile sections read: {', '.join(found) if found else 'none'}", sections=found)
    return described


def budget(ctx: BuildContext) -> Step:
    files = ctx.inventory.core + ctx.inventory.context
    tokens = round(sum(f.size for f in files) / 4)
    passes = len(ctx.inventory.core) + (1 if ctx.inventory.context else 0)
    yield log(
        f"Context budget: about {tokens:,} tokens of intake over {plural(passes, 'distillation pass', 'distillation passes')}, one file at a time",
        estimated_tokens=tokens,
        passes=passes,
    )
    return f"about {tokens:,} tokens"


MUSIC_PARTS = (("Purpose", "purpose statement"), ("Core Principles", "principle"), ("Value Logic", "value statement"), ("Decision Logic", "decision rule"))


def distil_music(ctx: BuildContext) -> Step:
    music = ctx.core[Category.MUSIC]
    yield llm(ctx.llm.call(f"distil {music.name}", music.content, (480, 900)))
    counts: dict[str, int] = {}
    for title, _ in MUSIC_PARTS:
        lines = assay.section_lines(music.content, title)
        counts[title] = assay.statements(lines) if lines is not None else 0
    yield log("Extracted " + ", ".join(plural(counts[t], word) for t, word in MUSIC_PARTS), **{t: counts[t] for t, _ in MUSIC_PARTS})
    empty = [t for t, _ in MUSIC_PARTS if not counts[t]]
    if empty:
        yield test(ctx, "T-04", "fail", f"nothing extracted from {', '.join(empty)}")
    else:
        yield test(ctx, "T-04", "pass", "Purpose, Core Principles, Value Logic and Decision Logic")
    return f"{sum(counts.values())} statements"


def distil_sections(category: Category, task: str, unit: str) -> Callable[[BuildContext], Step]:
    def step(ctx: BuildContext) -> Step:
        file = ctx.core[category]
        yield llm(ctx.llm.call(f"{task} {file.name}", file.content, (360, 760)))
        counts = {}
        for title in assay.coverage(file).found:
            counts[title] = assay.statements(assay.section_lines(file.content, title) or [])
        detail = "; ".join(f"{title} {n}" for title, n in counts.items())
        yield log(f"Distilled {file.name}: {plural(len(counts), unit)}, {plural(sum(counts.values()), 'statement')} ({detail})", **counts)
        return f"{plural(sum(counts.values()), 'statement')}"

    return step


def merge_context(ctx: BuildContext) -> Step:
    context = [f for f in ctx.inventory.context if f.name != FEEDBACK_NAME or ctx.iteration == 1]
    if not context:
        yield log("No Misc Context files to merge")
        return "none"
    yield llm(ctx.llm.call("merge Misc Context", "\n".join(f.content for f in context), (200, 480)))
    notes = sum(assay.statements(f.content.split("\n")) for f in context)
    yield log(f"Merged {plural(len(context), 'context file')}: {', '.join(f.name for f in context)} ({plural(notes, 'note')})", files=[f.name for f in context])
    return plural(len(context), "file")


def prior_findings(ctx: BuildContext) -> list[dict[str, Any]]:
    """Iteration 1's findings, advisories aside, from its kept log."""
    if ctx.prior is None:
        return []
    return [e.data for e in ctx.prior.log if e.type == "finding.raised" and not e.data.get("advisory")]


def ingest_feedback(ctx: BuildContext) -> Step:
    feedback = feedback_file(ctx.files)
    if feedback is None:
        yield log(f"No {FEEDBACK_NAME} to ingest")
    else:
        parts = segments(feedback.content)
        yield log(f"Observer feedback: {len(feedback.content):,} characters, {plural(len(parts), 'segment')}", characters=len(feedback.content), segments=len(parts))
    prior = prior_findings(ctx)
    yield log(f"Prior findings from iteration 1: {len(prior)}", prior_findings=[f.get("id") for f in prior])
    if prior:
        yield log(f"Planning corrections for all {plural(len(prior), 'prior finding')}")
    else:
        yield log("No prior findings, so there are no corrections to plan")
    return plural(len(prior), "prior finding")


# Phase 3: Synthesis


def draft(name: str, sources: tuple[Category, ...]) -> Callable[[BuildContext], Step]:
    def step(ctx: BuildContext) -> Step:
        source = ctx.text(*sources) + "\n".join(f.content for f in ctx.inventory.context)
        yield llm(ctx.llm.call(f"draft {name}", source, (560, 1400)))
        text = layers.outline(name, ctx.seed_name, ctx.iteration, ctx.fingerprint)
        ctx.drafts[name] = text
        count = len(layers.sections(name, ctx.iteration))
        yield log(f"Drafted {name} outline: {plural(count, 'section')}, {len(text.encode('utf-8')):,} bytes", sections=list(layers.sections(name, ctx.iteration)))
        if name == "protection.md" and ctx.iteration == 2:
            classes = sorted({str(f.get("category")) for f in prior_findings(ctx)})
            if classes:
                yield log(f"Learned rules for protection.md: {plural(len(classes), 'rule')}, one per finding class ({', '.join(classes)})", classes=classes)
            else:
                yield log("Learned rules for protection.md: none, iteration 1 recorded no findings", classes=[])
        return f"{plural(count, 'section')}"

    return step


def manifest(ctx: BuildContext) -> Step:
    ctx.manifest = layers.manifest(ctx.seed_name, ctx.iteration, ctx.fingerprint, ctx.drafts)
    yield log(f'Seed manifest: "{ctx.seed_name}", iteration {ctx.iteration}, 3 layers, fingerprint {ctx.fingerprint}', manifest=ctx.manifest)
    problems = layers.manifest_problems(ctx.manifest)
    if problems:
        yield test(ctx, "T-05", "fail", "; ".join(problems))
    else:
        yield test(ctx, "T-05", "pass", "seed, iteration, fingerprint and 3 layers with sizes and digests")
    return "assembled"


# Phase 4: Cross-Examination


def review(task: str, names: tuple[str, ...]) -> Callable[[BuildContext], Step]:
    def step(ctx: BuildContext) -> Step:
        yield llm(ctx.llm.call(task, "\n".join(ctx.drafts[n] for n in names) + ctx.text(Category.MUSIC), (240, 640)))
        yield log(f"Reviewer read {' and '.join(names)} against the distilled intake (simulated)")
        return "reviewed"

    return step


def resolve(ctx: BuildContext) -> Step:
    yield log("Contradictions between drafts: 0 (simulated reviewer)", contradictions=0)
    yield test(ctx, "T-06", "pass", "0 contradictions (simulated reviewer)", simulated=True)
    return "0 contradictions"


def signoff(ctx: BuildContext) -> Step:
    yield log(f"Drafts signed off: {', '.join(ctx.drafts)}")
    return "signed off"


# Phase 5: Germination Trial


def dry_run(ctx: BuildContext) -> Step:
    yield log("Dry run on the micro dataset: drafts applied, output produced (simulated)")
    yield test(ctx, "T-07", "pass", "completed (simulated)", simulated=True)
    return "completed"


def descriptor_digest(desc: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(desc, sort_keys=True).encode("utf-8")).hexdigest()[:6]


def data_swap(ctx: BuildContext) -> Step:
    """T-08 (FR-T-2, D-58): the dashboard's descriptor and query engine on the primary and the
    alternate estate. Passes when both payloads are structurally valid and share one structure."""
    desc = dashboard.descriptor(ctx.iteration)
    shapes = []
    invalid: list[str] = []
    for name in DATASETS:
        data = dataset(name)
        payload = dashboard.build(desc, data)
        problems = structure.problems(desc, payload, data)
        shapes.append(structure.shape(payload))
        invalid += [f"{name}: {p}" for p in problems]
        summary = data.summary()
        yield log(
            f"{data.title}: {summary['seats']:,} seats, {plural(summary['products'], 'product')}, {plural(summary['vendors'], 'vendor')}; "
            f"payload for {plural(len(payload['panels']), 'panel')}, {plural(len(problems), 'structural problem')}",
            dataset=name,
            seats=summary["seats"],
            products=summary["products"],
            vendors=summary["vendors"],
            problems=problems,
        )
    same = all(shape == shapes[0] for shape in shapes)
    digest = descriptor_digest(desc)
    yield log(
        f"Same descriptor ({digest}) and query engine on {plural(len(DATASETS), 'estate')}; payload structure "
        + ("identical" if same else "differs"),
        descriptor=digest,
        same_structure=same,
    )
    if invalid or not same:
        detail = "; ".join(invalid) if invalid else "payload structure differs between the estates"
        yield test(ctx, "T-08", "fail", detail)
        return "failed"
    yield test(ctx, "T-08", "pass", "same descriptor and query engine on both estates, both payloads structurally valid")
    return "logic unchanged"


def output_shape(ctx: BuildContext) -> Step:
    mismatched = [
        name for name, text in ctx.drafts.items()
        if [s.title for s in assay.sections(text) if s.level == 2] != list(layers.sections(name, ctx.iteration))
    ]
    if mismatched:
        yield log(f"Output shape: {', '.join(mismatched)} do not match their layer sections", "WARN", mismatched=mismatched)
        return "mismatch"
    yield log(f"Output shape: every draft has its layer's sections in order ({plural(len(ctx.drafts), 'layer')})")
    return "as expected"


# Phase 6: Containment


def manifest_bytes(ctx: BuildContext) -> bytes:
    return json.dumps(ctx.manifest, ensure_ascii=False, indent=2).encode("utf-8")


def handshake(ctx: BuildContext) -> Step:
    yield api(ctx.seed.health())
    created = ctx.seed.create_seed(ctx.manifest)
    ctx.seed_id = created.body["seed_id"]
    yield api(created)
    return f"seed {ctx.seed_id}"


def sandbox(ctx: BuildContext) -> Step:
    call = ctx.seed.provision_sandbox(ctx.seed_id)
    ctx.sandbox_id = call.body["sandbox_id"]
    yield api(call)
    yield log(f"Sandbox {ctx.sandbox_id} provisioned (isolated, no egress, simulated)", sandbox_id=ctx.sandbox_id)
    return ctx.sandbox_id


def upload(ctx: BuildContext) -> Step:
    files = {**{n: t.encode("utf-8") for n, t in ctx.drafts.items()}, "manifest.json": manifest_bytes(ctx)}
    for name, content in files.items():
        call = ctx.seed.upload(ctx.sandbox_id, name, content)
        ctx.uploads[name] = call.body["sha256"]
        yield api(call, 1.0)
    total = sum(len(c) for c in files.values())
    yield log(f"Uploaded {plural(len(files), 'file')}, {total:,} bytes", files=list(files), bytes=total)
    return plural(len(files), "file")


def checksums(ctx: BuildContext) -> Step:
    local = {**{n: t.encode("utf-8") for n, t in ctx.drafts.items()}, "manifest.json": manifest_bytes(ctx)}
    wrong = [name for name, content in local.items() if ctx.uploads.get(name) != hashlib.sha256(content).hexdigest()]
    yield log(f"Checksums compared: {plural(len(local), 'file')}, sha256")
    if wrong:
        yield test(ctx, "T-09", "fail", f"mismatch on {', '.join(wrong)}")
    else:
        yield test(ctx, "T-09", "pass", f"{len(local)} of {len(local)} match")
    return f"{len(local) - len(wrong)} of {len(local)} match"


# Phase 7: Planting (Seed v0.1 INIT)


def plant(ctx: BuildContext) -> Step:
    call = ctx.seed.plant(ctx.seed_id, list(ctx.drafts))
    yield api(call)
    yield log(f"Planting: three layers planted, Seed state {call.body['state']} (simulated Seed v0.1)", state=call.body["state"])
    return call.body["state"]


def headings(ctx: BuildContext) -> Step:
    for name, text in ctx.drafts.items():
        parts = assay.sections(text)
        sections = [s.title for s in parts if s.level == 2]
        yield log(f"{name}: {plural(len(parts), 'heading')}, {plural(len(sections), 'section')}", layer=name, headings=len(parts), sections=sections)
    return plural(len(ctx.drafts), "layer")


_BOLD_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\*\*(.+?)\*\*")


def declared_sources(environment: IntakeFile | None) -> list[str]:
    """Systems the Data Layer names as bold list items, in order (the sample's "Sources")."""
    lines = assay.section_lines(environment.content, "Data Layer") if environment else None
    names: list[str] = []
    for line in lines or []:
        match = _BOLD_ITEM.match(line)
        name = match.group(1).strip().rstrip(":").strip() if match else ""
        if name and name not in names:
            names.append(name)
    return names


def stack(ctx: BuildContext) -> Step:
    sources = declared_sources(ctx.core.get(Category.ENVIRONMENT))
    environment = ctx.name(Category.ENVIRONMENT)
    if sources:
        yield log(f"Declared stack from {environment}, Data Layer: {', '.join(sources)} (declared, not yet verified)", systems=sources)
    else:
        yield log(f"Declared stack: {environment} names no sources in its Data Layer", systems=[])
    call = ctx.seed.status(ctx.seed_id)
    yield api(call)
    ready = call.body.get("state") == "INITIALIZED"
    yield test(ctx, "T-10", "pass" if ready else "fail", f"Seed reports {call.body.get('state')} (simulated)", simulated=True)
    return plural(len(sources), "system")


# Phase 8: Seeding & Life (D-26): Discovery, Assessment, Implementation, Cleanup, Life


def gate(ctx: BuildContext, gate_id: str, kind: str, stage: str, resolution: str, basis: tuple[tuple[Category, str], ...]) -> Beat:
    """Auto-resolve one Seed v0.1 request (FR-B-5, seed-reuse-notes.md §4.2). The basis is the
    first listed heading the intake has; without one the gate resolves on default."""
    cited = None
    for category, wanted in basis:
        file = ctx.core.get(category)
        for part in assay.sections(file.content) if file else []:
            if wanted in assay.key(part.title):
                cited = {"file": file.name, "file_id": file.id, "section": part.title, "line": part.line}
                break
        if cited:
            break
    ctx.gates.append(gate_id)
    because = f"Basis: {cited['file']}, {cited['section']}" if cited else "No matching section in Knowledge, so it resolved on default"
    return Beat(
        2.0,
        [
            event(
                "gate.auto_resolved",
                f"Gate {gate_id} ({kind}) auto-resolved: {resolution}. {because}",
                "INFO",
                gate_id,
                gate=gate_id,
                kind=kind,
                stage=stage,
                resolution=resolution,
                basis=cited,
            )
        ],
    )


def raised(gate_id: str, kind: str, state: str) -> Beat:
    return log(f"Seed v0.1 raised request {gate_id} ({kind}); state {state} (simulated)", request=gate_id, kind=kind, state=state)


def discovery(ctx: BuildContext) -> Step:
    yield api(ctx.seed.advance(ctx.seed_id, "discovery", "DISCOVERING"))
    yield log("Discovery: reading the declared sources (simulated)")
    yield raised(GATES[0], "credentials", "DISCOVERY_BLOCKED")
    yield gate(
        ctx,
        GATES[0],
        "credentials",
        "discovery",
        "sandbox read-only credential issued (simulated), values not stored",
        ((Category.ENVIRONMENT, "protection"), (Category.ENVIRONMENT, "data")),
    )
    yield api(ctx.seed.answer(ctx.seed_id, GATES[0], {"username": "", "password": ""}))
    yield log("One endpoint timed out; retried and recovered (simulated)", "WARN")
    yield api(ctx.seed.advance(ctx.seed_id, "discovery/complete", "DISCOVERY_COMPLETE"))
    return "complete"


def assessment(ctx: BuildContext) -> Step:
    yield api(ctx.seed.advance(ctx.seed_id, "assessment", "ASSESSING"))
    yield log(f"Assessment: {ctx.seed_name} graded PARTIAL (simulated)", potential="PARTIAL")
    yield raised(GATES[1], "approval", "AWAITING_APPROVAL")
    yield gate(
        ctx,
        GATES[1],
        "approval",
        "assessment",
        f"approve {ctx.seed_name} at potential PARTIAL",
        ((Category.MUSIC, "decision logic"), (Category.MUSIC, "value logic")),
    )
    yield api(ctx.seed.answer(ctx.seed_id, GATES[1], {"decision": "approve"}))
    return "graded PARTIAL, approved"


def implementation(ctx: BuildContext) -> Step:
    yield api(ctx.seed.advance(ctx.seed_id, "implementation", "IMPLEMENTING"))
    yield log(f"Component {ctx.seed_name}: Pending, Building, Testing (simulated)")
    yield log(f"Component {ctx.seed_name}: Validated, Complete (simulated)")
    yield api(ctx.seed.advance(ctx.seed_id, "implementation/complete", "IMPLEMENTATION_COMPLETE"))
    return "component complete"


CLEANUP = ("consolidate-notes", "purge-scratch", "promote-interfaces", "retire-build-tools")


def cleanup(ctx: BuildContext) -> Step:
    yield raised(GATES[2], "confirmation", "IMPLEMENTATION_COMPLETE")
    yield gate(
        ctx,
        GATES[2],
        "confirmation",
        "cleanup",
        "close seeding",
        ((Category.ENVIRONMENT, "protection"), (Category.MUSIC, "decision logic")),
    )
    yield api(ctx.seed.answer(ctx.seed_id, GATES[2], {"acknowledged": True, "choice": "close"}))
    for operation in CLEANUP:
        yield api(ctx.seed.cleanup(ctx.seed_id, operation), 1.0)
    yield log("Cleanup: 4 operations done, seed consumed (simulated)", operations=list(CLEANUP))
    return "seed consumed"


def life(ctx: BuildContext) -> Step:
    yield api(ctx.seed.advance(ctx.seed_id, "run", "READY_TO_RUN"))
    for block in range(3):
        weeks = (block * 4 + 1, block * 4 + 4)
        yield api(ctx.seed.collect(ctx.seed_id, weeks), 1.0)
        yield log(f"Life: weeks {weeks[0]} to {weeks[1]} of 12 collected, recalibration {block + 1} of 3 (simulated)")
    yield log("Life: caught up after 12 weeks (simulated)", weeks=12, recalibrations=3)
    resolved = [g for g in GATES if g in ctx.gates]
    if len(resolved) == len(GATES):
        yield test(ctx, "T-11", "pass", f"{len(GATES)} of {len(GATES)} auto-resolved")
    else:
        yield test(ctx, "T-11", "fail", f"{len(resolved)} of {len(GATES)} auto-resolved")
    yield test(ctx, "T-12", "pass", "component validated, 12 weeks collected (simulated)", simulated=True)
    return "caught up"


# Phases 9 and 10: validators arrive in M9 (D-51)


def pending(tests: tuple[str, ...], milestone: str = "M9") -> Callable[[BuildContext], Step]:
    def step(ctx: BuildContext) -> Step:
        for test_id in tests:
            yield not_run(ctx, test_id, "this validator", milestone)
        return "not run"

    return step


def collect_payload(ctx: BuildContext) -> Step:
    desc = dashboard.descriptor(ctx.iteration)
    data = dataset(dashboard.DEFAULT_DATASET)
    payload = dashboard.build(desc, data)
    yield log(
        f"Collected the {desc['title']} payload ({desc['variant']}): {plural(len(payload['panels']), 'panel')} at All products, "
        f"from {len(data.seats):,} seat rows in the {data.title.lower()}",
        dashboard=desc["id"],
        variant=desc["variant"],
        panels=len(payload["panels"]),
        seats=len(data.seats),
        descriptor=descriptor_digest(desc),
    )
    return f"{plural(len(payload['panels']), 'panel')}"


# Phase 11: Teardown & Report


def teardown(ctx: BuildContext) -> Step:
    yield api(ctx.seed.teardown(ctx.sandbox_id))
    yield log(f"Sandbox {ctx.sandbox_id} torn down, no residue (simulated)")
    yield test(ctx, "T-21", "pass", "no residue (simulated)", simulated=True)
    return "torn down"


def compile_report(ctx: BuildContext) -> Step:
    yield log("Report assembly arrives in M9; this build's events are kept with its record")
    return "not yet assembled"


def package(ctx: BuildContext) -> Step:
    total = sum(len(t.encode("utf-8")) for t in ctx.drafts.values()) + len(manifest_bytes(ctx))
    yield log(f"Seed files: {', '.join(ctx.drafts)} outlines and manifest.json, {total:,} bytes; full files and the zip arrive in M11")
    return "outlines ready"


STEPS: dict[str, Callable[[BuildContext], Step]] = {
    "assay.feedback-route": feedback_route,
    "assay.feedback-person": feedback_update(Category.PERSON),
    "assay.feedback-instrument": feedback_update(Category.INSTRUMENT_AWARENESS),
    "assay.feedback-environment": feedback_update(Category.ENVIRONMENT),
    "assay.feedback-music": feedback_update(Category.MUSIC, last=True),
    "assay.inventory": inventory,
    "assay.coverage": coverage,
    "assay.boundary": boundary_check,
    "assay.fingerprint": fingerprint,
    "distill.profile": profile,
    "distill.budget": budget,
    "distill.music": distil_music,
    "distill.person": distil_sections(Category.PERSON, "distil", "section"),
    "distill.environment": distil_sections(Category.ENVIRONMENT, "distil layers of", "layer"),
    "distill.context": merge_context,
    "distill.feedback": ingest_feedback,
    "synth.core": draft("core.md", (Category.MUSIC, Category.PERSON)),
    "synth.adaptation": draft("adaptation.md", (Category.ENVIRONMENT,)),
    "synth.protection": draft("protection.md", (Category.ENVIRONMENT, Category.INSTRUMENT_AWARENESS)),
    "synth.manifest": manifest,
    "xexam.core": review("review core.md", ("core.md",)),
    "xexam.layers": review("review adaptation.md and protection.md", ("adaptation.md", "protection.md")),
    "xexam.resolve": resolve,
    "xexam.signoff": signoff,
    "germ.dry-run": dry_run,
    "germ.data-swap": data_swap,
    "germ.shape": output_shape,
    "contain.handshake": handshake,
    "contain.sandbox": sandbox,
    "contain.upload": upload,
    "contain.checksums": checksums,
    "plant.layers": plant,
    "plant.headings": headings,
    "plant.stack": stack,
    "seeding.discovery": discovery,
    "seeding.assessment": assessment,
    "seeding.implementation": implementation,
    "seeding.cleanup": cleanup,
    "seeding.life": life,
    "probe.protection": pending(("T-13",)),
    "probe.malformed": pending(("T-14",)),
    "probe.latency": pending(("T-15",)),
    "harvest.collect": collect_payload,
    "harvest.numeric": pending(("T-16",)),
    "harvest.chart": pending(("T-17",)),
    "harvest.visual": pending(("T-18", "T-19")),
    "harvest.contrast": pending(("T-20",)),
    "report.teardown": teardown,
    "report.compile": compile_report,
    "report.package": package,
}


# Phases and the schedule


PHASE_LEVELS = {"passed": "PASS", "findings": "WARN", "incomplete": "TEST", "failed": "FAIL"}


def phase_result(ctx: BuildContext, phase: Phase) -> tuple[str, dict[str, str]]:
    """passed, findings (a finding that is not an advisory), incomplete (a test not run) or failed."""
    tests = {test_id: ctx.results.get(test_id, "not_run") for test_id, _ in phase.tests}
    if "fail" in tests.values():
        return "failed", tests
    if any(f["phase"] == phase.id and not f.get("advisory") for f in ctx.findings):
        return "findings", tests
    if "not_run" in tests.values():
        return "incomplete", tests
    return "passed", tests


def phase_beats(ctx: BuildContext, index: int, phase: Phase) -> Generator[Beat, None, None]:
    yield Beat(0, [event("phase.started", f"Phase {index + 1} of {len(PHASES)}: {phase.name}", index=index + 1, name=phase.name, weight=phase.weight)])
    for step in phase.steps_for(ctx.iteration):
        step_id = f"{phase.id}.{step.id}"
        yield Beat(0, [{**event("step.started", step.name, name=step.name), "step": step_id}])
        summary = yield from _tagged(STEPS[step_id](ctx), step_id)
        yield Beat(0, [{**event("step.completed", f"{step.name}: {summary or 'done'}", name=step.name, summary=summary), "step": step_id}])
    result, tests = phase_result(ctx, phase)
    counts = {status: list(tests.values()).count(status) for status in ("pass", "warn", "fail", "not_run")}
    detail = result
    if result == "incomplete":
        detail = f"incomplete, {counts['not_run']} of {len(tests)} tests not run"
    elif result == "failed":
        detail = f"failed ({', '.join(t for t, s in tests.items() if s == 'fail')})"
    yield Beat(0, [event("phase.completed", f"{phase.name}: {detail}", PHASE_LEVELS[result], index=index + 1, name=phase.name, result=result, tests=tests)])


def _tagged(steps: Step, step_id: str) -> Step:
    """The step's beats with its id on each event; returns the step's summary."""
    while True:
        try:
            beat = next(steps)
        except StopIteration as done:
            return done.value
        beat.events = [{**e, "step": step_id} for e in beat.events]
        yield beat


def build_summary(ctx: BuildContext) -> tuple[str, str, dict[str, Any]]:
    statuses = [ctx.results.get(t, "not_run") for t in TEST_NAMES]
    counts = {status: statuses.count(status) for status in ("pass", "warn", "fail", "not_run")}
    findings = [f for f in ctx.findings if not f.get("advisory")]
    advisories = [f for f in ctx.findings if f.get("advisory")]
    passed = counts["pass"] + counts["warn"]
    parts = [f"{passed} tests passed"]
    if counts["not_run"]:
        parts.append(f"{counts['not_run']} not run")
    if counts["fail"]:
        parts.append(f"{counts['fail']} failed")
    message = f"Build completed: {', '.join(parts)}; {plural(len(findings), 'finding')}, {plural(len(advisories), 'boundary advisory', 'boundary advisories')}"
    level = "FAIL" if counts["fail"] else "WARN" if findings else "INFO" if counts["not_run"] else "PASS"
    data = {
        "status": "completed",
        "seed_name": ctx.seed_name,
        "fingerprint": ctx.fingerprint,
        "tests": {t: ctx.results.get(t, "not_run") for t in TEST_NAMES},
        "counts": counts,
        "findings": [f["id"] for f in findings],
        "advisories": [f["id"] for f in advisories],
        "gates": list(ctx.gates),
        "sim_seconds": BUDGET_SECONDS,
    }
    return message, level, data


def script(ctx: BuildContext) -> list[Beat]:
    """Every beat of the build, in order, each with its sim_t and phase index."""
    record = ctx.record()
    beats = [Beat(0, [event("build.started", f'Build started: iteration {ctx.iteration}, seed "{ctx.seed_name}"', build=record.summary())])]
    start = 0.0
    done = 0
    for index, phase in enumerate(PHASES):
        own = list(phase_beats(ctx, index, phase))
        total = sum(beat.weight for beat in own)
        clock = 0.0
        for beat in own:
            beat.phase_index = index
            beat.sim_t = round(start + clock / total * phase.seconds, 3)
            clock += beat.weight
            for e in beat.events:
                e.setdefault("phase", phase.id)
        done += phase.weight
        start = BUDGET_SECONDS * done / TOTAL_WEIGHT
        own[-1].sim_t = round(start, 3)  # phase.completed closes the phase's time
        beats += own
    message, level, data = build_summary(ctx)
    beats.append(Beat(0, [event("build.completed", message, level, **data)], phase_index=len(PHASES) - 1, sim_t=BUDGET_SECONDS))
    return beats
