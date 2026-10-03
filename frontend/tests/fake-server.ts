// An in-memory stand-in for the intake API (D-34, D-35), the demo actions (D-46) and builds
// (D-48, D-49), for page tests. It keeps the server's rules that the page relies on (one file
// per core category unless `replace`, trimmed names, the lock while a build runs, Load sample
// only on an empty intake unless `replace`, Start Build only with four filled core files and
// no build running, skip only while one runs) and records every request. A started build stays
// running until a test ends it; no engine runs here. Canned refusals (413, 415) are queued
// with `refuseNext`, as the real checks live in the backend's tests. Load sample serves the
// real sample files from backend/seedfoundry/sample. A build's events, for the Build page
// (D-54), are whatever a test puts in `buildEvents`.

import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { vi } from 'vitest'
import type { LabEvent } from '../src/events'
import type { IntakeFile } from '../src/intake'
import type { Build, Snapshot } from '../src/stores/lab'

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
  iteration = 1
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
        approval: null,
      }),
    )
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
    const eventsMatch = path.match(/^\/api\/builds\/([^/]+)\/events$/)
    if (method === 'GET' && eventsMatch) {
      const build = this.builds.find((b) => b.id === eventsMatch[1])
      if (!build) return refusal(404, 'build_not_found', `No build with id ${eventsMatch[1]}.`)
      return { status: 200, body: { build_id: build.id, status: build.status, seq: this.seq, events: this.buildEvents.get(build.id) ?? [] } }
    }
    if (method === 'GET' && path === '/api/demo/speed') return { status: 200, body: { speed: this.speed } }
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
    if (method === 'POST' && path === '/api/builds') {
      if (running) return refusal(409, 'build_running', 'A build is running. Wait for it to finish, or use Reset to start.')
      const missing = [...CORE].filter((c) => !this.files.some((f) => f.category === c && f.content.trim()))
      if (missing.length) {
        const labels = missing.map((c) => LABELS[c]).join(', ')
        return refusal(409, 'core_files_missing', `Start Build needs every core file. Missing: ${labels}.`, { missing })
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
