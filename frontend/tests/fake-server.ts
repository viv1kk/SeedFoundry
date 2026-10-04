// An in-memory stand-in for the intake API (D-34, D-35), the demo actions (D-46) and builds
// (D-48, D-49), for page tests. It keeps the server's rules that the page relies on (one file
// per core category unless `replace`, trimmed names, the lock while a build runs, Load sample
// only on an empty intake unless `replace`, Start Build only with four filled core files and
// no build running, skip only while one runs) and records every request. A started build stays
// running until a test ends it; no engine runs here. Canned refusals (413, 415) are queued
// with `refuseNext`, as the real checks live in the backend's tests. Load sample serves the
// real sample files from backend/seedfoundry/sample. A build's events, for the Build page
// (D-54), are whatever a test puts in `buildEvents`. The dashboard (D-56) replays real responses
// the backend wrote to tests/fixtures/dashboard/iteration-<n>/, one set per iteration (iteration 1
// is the rough dashboard, iteration 2 the polished one; backend/tests/dashboard_fixtures.py, checked
// against the backend by test_dashboard.py); a drill path with no fixture is refused as the
// server refuses a path the data does not have. A completed build's report (D-64) is the report the
// backend assembled for the sample's build of that iteration (tests/fixtures/reports/, written by
// backend/tests/report_fixtures.py and checked by test_report.py), with the build's own id. The
// rebuild (D-67, D-81) is POST /api/builds with the next iteration and the feedback: it keeps the
// server's rules (feedback that is not blank, a completed current iteration) and saves the feedback
// file of the rejected iteration with the build, in one step; Prefill's text is the real demo
// feedback file for that iteration. Iteration 3 on replays iteration 2's fixtures (D-81). Approve (D-73)
// keeps the server's rules (the current iteration's completed build, once, with no build running)
// and the Seed page's data is what the backend assembled for that approval path
// (tests/fixtures/seed/, written by backend/tests/seed_fixtures.py and checked by test_seed.py), with
// the approved build's own id; a build after approval is refused, and Reset clears it.

import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { vi } from 'vitest'
import type { LabEvent } from '../src/events'
import type { IntakeFile } from '../src/intake'
import type { Approval, Build, Snapshot } from '../src/stores/lab'

export const CATEGORIES = {
  categories: [
    { id: 'person', label: 'Person', core: true, description: 'Who does the work.' },
    { id: 'instrument_awareness', label: 'Instrument Awareness', core: true, description: 'Which tool it uses.' },
    { id: 'environment', label: 'Environment', core: true, description: 'Where the work happens.' },
    { id: 'music', label: 'Music', core: true, description: 'Why the work exists.' },
    { id: 'misc_context', label: 'Misc Context', core: false, description: 'Anything else worth knowing.' },
  ],
  filename_hints: {
    'person.md': 'person',
    'player.md': 'person',
    'instrument-awareness.md': 'instrument_awareness',
    'instrument_awareness.md': 'instrument_awareness',
    'environment.md': 'environment',
    'music.md': 'music',
  },
  max_file_bytes: 1048576,
}

const SAMPLE_DIR = resolve(__dirname, '../../backend/seedfoundry/sample')

/** The sample Seed in load order, line ends normalised as the server stores them. */
export const SAMPLE = (
  [
    ['person.md', 'person'],
    ['instrument-awareness.md', 'instrument_awareness'],
    ['environment.md', 'environment'],
    ['music.md', 'music'],
    ['vendor-notes.md', 'misc_context'],
  ] as const
).map(([name, category]) => ({
  name,
  category,
  content: readFileSync(resolve(SAMPLE_DIR, name), 'utf8').replace(/\r\n?/g, '\n'),
}))

/** The demo's observer feedback (Prefill, D-68), as the server serves it. */
export const DEMO_FEEDBACK = readFileSync(resolve(SAMPLE_DIR, 'rebuild/observer-feedback-iteration-1.md'), 'utf8').replace(/\r\n?/g, '\n')

export const FEEDBACK_NAME = 'observer-feedback-iteration-1.md'
export const LATER_FEEDBACK = readFileSync(resolve(SAMPLE_DIR, 'rebuild/observer-feedback-later.md'), 'utf8').replace(/\r\n?/g, '\n')
const feedbackName = (rejected: number) => `observer-feedback-iteration-${rejected}.md`
/** Iteration 3 on has no fixtures of its own: it plays iteration 2's outcome (D-81). */
const fixtureIteration = (iteration: number) => Math.min(iteration, 2)

const DASHBOARD_DIR = resolve(__dirname, 'fixtures/dashboard')

/** Fixture file for a dashboard request: drill path, then page and sort. */
const DASHBOARD_FIXTURES: Record<string, string> = {
  '': 'root.json',
  '|2': 'root-page-2.json',
  '|1|days_idle|asc': 'root-days-idle-asc.json',
  '|1|days_idle|desc': 'root-days-idle-desc.json',
  microsoft: 'vendor.json',
  'microsoft/microsoft-365-e3': 'vendor-product.json',
  'microsoft.microsoft-365-e3': 'product-step.json',
  'microsoft.microsoft-365-e3.unused': 'leaf.json',
  'microsoft/microsoft-365-e3/unused': 'leaf-steps.json',
}

/** A dashboard response the backend wrote, for an iteration (1 rough, 2 polished, D-60). */
export function dashboardFixture(iteration: number, name: string): Record<string, unknown> {
  return JSON.parse(readFileSync(resolve(DASHBOARD_DIR, `iteration-${iteration}`, name), 'utf8'))
}

const REPORT_DIR = resolve(__dirname, 'fixtures/reports')

/** The report the backend assembled for the sample's build of an iteration (D-64). */
export function reportFixture(iteration: number): Record<string, unknown> {
  return JSON.parse(readFileSync(resolve(REPORT_DIR, `iteration-${iteration}.json`), 'utf8'))
}

const SEED_DIR = resolve(__dirname, 'fixtures/seed')

/** The Seed page's data the backend assembled for approving the sample's iteration 1 or 2 (D-73). */
export function seedFixture(iteration: number): Record<string, unknown> {
  return JSON.parse(readFileSync(resolve(SEED_DIR, `iteration-${iteration}.json`), 'utf8'))
}

/** The sample's iteration 1 build, every event as the backend kept it (wall_ts fixed). */
export function sampleBuildEvents(): LabEvent[] {
  return JSON.parse(readFileSync(resolve(REPORT_DIR, 'iteration-1-events.json'), 'utf8'))
}

const LABELS: Record<string, string> = Object.fromEntries(CATEGORIES.categories.map((c) => [c.id, c.label]))
const CORE = new Set(CATEGORIES.categories.filter((c) => c.core).map((c) => c.id))

export interface Call {
  method: string
  path: string
  query: Record<string, string>
  body: unknown
}

interface Reply {
  status: number
  body?: unknown
}

const encoder = new TextEncoder()

function refusal(status: number, code: string, message: string, extra: Record<string, unknown> = {}): Reply {
  return { status, body: { detail: { code, message, ...extra } } }
}

export class FakeServer {
  files: IntakeFile[] = []
  builds: Build[] = []
  buildEvents = new Map<string, LabEvent[]>()
  /** Fields to put over the fixture report of an iteration, for a test that needs another report. */
  reportPatches = new Map<number, Record<string, unknown>>()
  /** Fields to put over the Seed page fixture of an iteration (a hostile file for Preview, say). */
  seedPatches = new Map<number, Record<string, unknown>>()
  iteration = 1
  approval: Approval | null = null
  speed = 1
  seq = 0
  nextId = 1
  nextBuild = 1
  calls: Call[] = []
  /** Requests whose reply is held until `release()`. */
  held: { resolve: () => void }[] = []
  holdWrites = false
  private refusals: { match: (call: Call) => boolean; reply: Reply }[] = []

  readonly fetch = vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
    const url = new URL(String(input), 'http://127.0.0.1:5273')
    const method = (init.method ?? 'GET').toUpperCase()
    let body: unknown = init.body
    if (typeof body === 'string') body = JSON.parse(body)
    else if (body && typeof (body as Blob).text === 'function') body = await (body as Blob).text()
    const call: Call = { method, path: url.pathname, query: Object.fromEntries(url.searchParams), body }
    this.calls.push(call)
    if (method !== 'GET' && this.holdWrites) await new Promise<void>((resolve) => this.held.push({ resolve }))
    const reply = this.handle(call)
    return {
      ok: reply.status < 400,
      status: reply.status,
      json: async () => JSON.parse(JSON.stringify(reply.body ?? null)),
    } as Response
  })

  constructor(files: Partial<IntakeFile>[] = []) {
    for (const file of files) this.add(file.name ?? 'notes.md', file.category ?? 'misc_context', file.content ?? '')
  }

  add(name: string, category: string, content = ''): IntakeFile {
    const file = { id: `f-${this.nextId++}`, name, category, content, size: encoder.encode(content).length }
    this.files.push(file)
    return file
  }

  snapshot(): Snapshot {
    return JSON.parse(
      JSON.stringify({
        schema: 1,
        seq: this.seq,
        iteration: this.iteration,
        next_file_id: this.nextId,
        next_build_id: this.nextBuild,
        intake: { files: this.files },
        builds: this.builds,
        approval: this.approval,
      }),
    )
  }

  /** The approved Seed's page data: the fixture for its iteration, with this approval's build and time. */
  seedPage(): Record<string, unknown> {
    const page = { ...seedFixture(fixtureIteration(this.approval!.iteration)), ...this.seedPatches.get(this.approval!.iteration) }
    return { ...page, approval: { ...(page.approval as object), ...this.approval } }
  }

  /** The next request that matches gets this refusal instead. */
  refuseNext(match: (call: Call) => boolean, status: number, code: string, message: string): void {
    this.refusals.push({ match, reply: refusal(status, code, message) })
  }

  release(): void {
    this.held.splice(0).forEach((h) => h.resolve())
  }

  writes(): Call[] {
    return this.calls.filter((c) => c.method !== 'GET')
  }

  private find(id: string): IntakeFile | undefined {
    return this.files.find((f) => f.id === id)
  }

  private claim(category: string, replace: boolean, newcomer: string, keepId?: string): Reply | null {
    if (!CORE.has(category)) return null
    const existing = this.files.find((f) => f.category === category && f.id !== keepId)
    if (!existing) return null
    if (!replace) {
      return refusal(409, 'core_slot_taken', `${LABELS[category]} already has ${existing.name}. Replace it with ${newcomer}?`, {
        existing: { id: existing.id, name: existing.name, category, size: existing.size },
      })
    }
    this.files = this.files.filter((f) => f !== existing)
    this.seq++
    return null
  }

  private dashboard(query: Record<string, string>): Reply {
    const drill = query.drill ?? ''
    const page = query.page ?? '1'
    const key = page === '1' && !query.sort ? drill : [drill, page, query.sort, query.direction].filter((part) => part !== undefined).join('|')
    const name = DASHBOARD_FIXTURES[key]
    if (!name) {
      if (drill && !(drill in DASHBOARD_FIXTURES)) return refusal(404, 'drill_not_found', `No vendor '${drill.split(/[./]/)[0]}' in the data (drill path '${drill}').`)
      return refusal(500, 'no_fixture', `The fake server has no dashboard fixture for ${key}.`)
    }
    return { status: 200, body: dashboardFixture(fixtureIteration(Number(query.iteration)), name) }
  }

  private handle(call: Call): Reply {
    const index = this.refusals.findIndex((r) => r.match(call))
    if (index >= 0) return this.refusals.splice(index, 1)[0].reply
    const { method, path } = call
    if (method === 'GET' && path === '/api/state') return { status: 200, body: this.snapshot() }
    if (method === 'GET' && path === '/api/intake/categories') return { status: 200, body: CATEGORIES }
    const locked = this.builds.some((b) => b.status === 'running')
    const fileMatch = path.match(/^\/api\/intake\/files\/([^/]+)$/)
    if (method === 'GET' && fileMatch) {
      const file = this.find(fileMatch[1])
      return file ? { status: 200, body: file } : refusal(404, 'file_not_found', `No file with id ${fileMatch[1]}.`)
    }
    if (method === 'GET' && path === '/api/dashboards/license-optimization') return this.dashboard(call.query)
    const eventsMatch = path.match(/^\/api\/builds\/([^/]+)\/events$/)
    if (method === 'GET' && eventsMatch) {
      const build = this.builds.find((b) => b.id === eventsMatch[1])
      if (!build) return refusal(404, 'build_not_found', `No build with id ${eventsMatch[1]}.`)
      return { status: 200, body: { build_id: build.id, status: build.status, seq: this.seq, events: this.buildEvents.get(build.id) ?? [] } }
    }
    const reportMatch = path.match(/^\/api\/builds\/([^/]+)\/report$/)
    if (method === 'GET' && reportMatch) {
      const build = this.builds.find((b) => b.id === reportMatch[1])
      if (!build) return refusal(404, 'build_not_found', `No build with id ${reportMatch[1]}.`)
      if (build.status !== 'completed') return refusal(409, 'report_not_ready', `Build ${build.id} has not completed, so it has no report.`)
      const fixture = reportFixture(fixtureIteration(build.iteration))
      return { status: 200, body: { ...fixture, ...this.reportPatches.get(build.iteration), build_id: build.id, iteration: build.iteration } }
    }
    if (method === 'GET' && path === '/api/seed') {
      if (!this.approval) return refusal(404, 'seed_not_approved', 'No Seed is approved yet. Approve a completed build from its report first.')
      return { status: 200, body: this.seedPage() }
    }
    if (method === 'GET' && path === '/api/demo/speed') return { status: 200, body: { speed: this.speed } }
    if (method === 'GET' && path === '/api/demo/feedback') {
      const rejected = Number(call.query.rejected ?? 1)
      return { status: 200, body: { name: feedbackName(rejected), content: rejected > 1 ? LATER_FEEDBACK : DEMO_FEEDBACK } }
    }
    if (method === 'POST' && path === '/api/demo/speed') {
      const speed = (call.body as { speed?: number }).speed
      if (speed !== 1 && speed !== 2 && speed !== 4) return { status: 422, body: { detail: [] } }
      this.speed = speed
      return { status: 200, body: { speed } }
    }
    const running = this.builds.find((b) => b.status === 'running')
    if (method === 'POST' && path === '/api/demo/skip') {
      if (!running) return refusal(409, 'no_build_running', 'No build is running, so there is nothing to skip.')
      const to = (call.body as { to?: string }).to
      return { status: 200, body: to === 'phase' ? { skipping: 'phase', phase: 'assay', name: 'Assay' } : { skipping: 'build' } }
    }
    if (method === 'POST' && path === '/api/seed/approve') {
      if (this.approval) return refusal(409, 'seed_approved', `This Seed is already approved at iteration ${this.approval.iteration}. Use Reset to start a new one.`)
      const id = (call.body as { build_id?: string }).build_id
      const build = this.builds.find((b) => b.id === id)
      if (!build) return refusal(404, 'build_not_found', `No build with id ${id}.`)
      if (running) return refusal(409, 'build_running', 'A build is running. Approve once it has finished.')
      if (build.status !== 'completed') return refusal(409, 'report_not_ready', `Build ${build.id} has not completed, so there is nothing to approve.`)
      if (build.iteration !== this.iteration) {
        return refusal(409, 'iteration_superseded', `Iteration ${build.iteration + 1} was rebuilt from this build, so iteration ${this.iteration} is the one to approve.`)
      }
      this.approval = { iteration: build.iteration, build_id: build.id, approved_at: '2026-10-04T12:00:00.000+00:00' }
      this.seq++
      return { status: 201, body: this.seedPage() }
    }
    if (method === 'POST' && path === '/api/builds') {
      if (this.approval) return refusal(409, 'seed_approved', 'This Seed is approved, so it is not built again. Use Reset to start a new one.')
      if (running) return refusal(409, 'build_running', 'A build is running. Wait for it to finish, or use Reset to start.')
      const missing = [...CORE].filter((c) => !this.files.some((f) => f.category === c && f.content.trim()))
      if (missing.length) {
        const labels = missing.map((c) => LABELS[c]).join(', ')
        return refusal(409, 'core_files_missing', `Start Build needs every core file. Missing: ${labels}.`, { missing })
      }
      const body = (call.body ?? {}) as { iteration?: number; feedback?: string }
      const current = this.iteration
      const rebuilding = body.iteration === current + 1
      if (body.feedback !== undefined && !rebuilding) {
        const target = body.iteration ?? current
        return refusal(409, 'wrong_iteration', `Observer feedback starts iteration ${current + 1} from iteration ${current}'s report; this request names iteration ${target}.`)
      }
      if (rebuilding) {
        const next = current + 1
        if (!this.builds.some((b) => b.iteration === current && b.status === 'completed')) {
          return refusal(409, `iteration_${current}_not_built`, `Iteration ${next} needs a completed iteration ${current} build.`)
        }
        if (!body.feedback?.trim()) return refusal(422, 'feedback_empty', `Start Rebuild needs observer feedback. Write what iteration ${next} should change first.`)
        const name = feedbackName(current)
        const existing = this.files.find((f) => f.category === 'misc_context' && f.name === name)
        if (existing) {
          existing.content = body.feedback
          existing.size = encoder.encode(body.feedback).length
        } else this.add(name, 'misc_context', body.feedback)
        this.iteration = next
        this.seq++
      }
      const build: Build = { id: `b-${this.nextBuild++}`, iteration: this.iteration, status: 'running', seed_name: 'License Optimization', phase: null, plan: [] }
      this.builds = [...this.builds.filter((b) => b.iteration !== build.iteration), build]
      this.seq++
      return { status: 201, body: build }
    }
    // Reset to start is allowed while a build runs (D-46).
    if (method === 'POST' && path === '/api/demo/reset') {
      const removed = { files_removed: this.files.length, builds_removed: this.builds.length }
      this.files = []
      this.builds = []
      this.approval = null
      this.iteration = 1
      this.seq++
      return { status: 200, body: removed }
    }
    if (method !== 'GET' && locked) return refusal(409, 'intake_locked', 'Knowledge files are read-only while a build runs.')
    if (method === 'POST' && path === '/api/demo/sample') {
      const count = this.files.length
      if (count && (call.body as { replace?: boolean }).replace !== true) {
        const files = count === 1 ? '1 file' : `${count} files`
        return refusal(409, 'intake_not_empty', `Knowledge has ${files}. Loading the sample Seed replaces them all.`, { files: count })
      }
      this.files = []
      this.seq += count + SAMPLE.length
      return { status: 201, body: SAMPLE.map((f) => this.add(f.name, f.category, f.content)) }
    }
    if (method === 'POST' && path === '/api/demo/clear') {
      const deleted = this.files.length
      this.files = []
      this.seq += deleted
      return { status: 200, body: { deleted } }
    }
    if (method === 'POST' && (path === '/api/intake/files' || path === '/api/intake/import')) {
      const json = (path === '/api/intake/import' ? {} : call.body) as Record<string, unknown>
      const name = String(path === '/api/intake/import' ? call.query.filename : json.name).trim()
      const category = String(path === '/api/intake/import' ? call.query.category : json.category)
      const replace = path === '/api/intake/import' ? call.query.replace === 'true' : json.replace === true
      const content = path === '/api/intake/import' ? String(call.body ?? '') : String(json.content ?? '')
      if (!name) return refusal(422, 'invalid_name', 'A file needs a name.')
      const taken = this.claim(category, replace, name)
      if (taken) return taken
      this.seq++
      return { status: 201, body: this.add(name, category, content) }
    }
    if (method === 'PATCH' && fileMatch) {
      const file = this.find(fileMatch[1])
      if (!file) return refusal(404, 'file_not_found', `No file with id ${fileMatch[1]}.`)
      const changes = call.body as Record<string, unknown>
      if (typeof changes.name === 'string') {
        const name = changes.name.trim()
        if (!name) return refusal(422, 'invalid_name', 'A file needs a name.')
        if (name.includes('/') || name.includes('\\')) return refusal(422, 'invalid_name', 'A file name cannot contain / or \\.')
        file.name = name
      }
      if (typeof changes.category === 'string' && changes.category !== file.category) {
        const taken = this.claim(changes.category, changes.replace === true, file.name, file.id)
        if (taken) return taken
        file.category = changes.category
      }
      if (typeof changes.content === 'string') {
        file.content = changes.content
        file.size = encoder.encode(file.content).length
      }
      this.seq++
      return { status: 200, body: file }
    }
    if (method === 'DELETE' && fileMatch) {
      const file = this.find(fileMatch[1])
      if (!file) return refusal(404, 'file_not_found', `No file with id ${fileMatch[1]}.`)
      this.files = this.files.filter((f) => f !== file)
      this.seq++
      return { status: 204 }
    }
    return refusal(404, 'not_found', `${method} ${path}`)
  }
}
