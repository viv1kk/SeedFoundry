// Live server state (D-38): GET /api/state, then GET /api/events after its seq.
// Intake events are applied in place (D-41): they carry no content (D-32), so a file whose
// content changed is fetched with GET /api/intake/files/{id}, unless the change is this
// client's own save, whose content it already has. Any other newer event, a gap in the seqs,
// an intake event that cannot be applied, and stream.resync re-fetch the snapshot, one
// request at a time. Build reducers arrive in M5 and M6.

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { EVENT_TYPES, type LabEvent } from '../events'
import { intakeApi, utf8Size, type FileSummary, type IntakeFile } from '../intake'

export type { IntakeFile } from '../intake'

export type BuildStatus = 'running' | 'completed' | 'interrupted'

export interface Build {
  id: string
  iteration: number
  status: BuildStatus
}

export interface Snapshot {
  schema: number
  seq: number
  iteration: number
  next_file_id: number
  intake: { files: IntakeFile[] }
  builds: Build[]
  approval: { iteration: number } | null
}

/** Exactly two iterations (D-6). */
export const ITERATIONS = 2

const RETRY_MS = 2000

function isSummary(value: unknown): value is FileSummary {
  if (!value || typeof value !== 'object') return false
  const file = value as Record<string, unknown>
  return typeof file.id === 'string' && typeof file.name === 'string' && typeof file.category === 'string' && typeof file.size === 'number'
}

export const useLabStore = defineStore('lab', () => {
  const snapshot = ref<Snapshot | null>(null)
  const status = ref<'idle' | 'connecting' | 'live' | 'offline'>('idle')

  /** The iteration of the latest build, or null before the first build. */
  const currentIteration = computed(() => {
    const builds = snapshot.value?.builds ?? []
    return builds.length ? builds[builds.length - 1].iteration : null
  })

  /** The build that holds intake read-only (FR-B-8), if any. */
  const runningBuild = computed(() => snapshot.value?.builds.find((build) => build.status === 'running') ?? null)

  const files = computed<IntakeFile[]>(() => snapshot.value?.intake.files ?? [])

  function file(id: string | null | undefined): IntakeFile | undefined {
    return id ? snapshot.value?.intake.files.find((f) => f.id === id) : undefined
  }

  let source: EventSource | null = null
  let fetching = false
  let stale = false

  // A content fetch is kept only if nothing newer reached that file meanwhile: a later fetch,
  // this client's own write, or a new snapshot.
  let generation = 0
  const loads = new Map<string, number>()

  function invalidate(id: string): void {
    loads.set(id, (loads.get(id) ?? 0) + 1)
  }

  async function refresh(): Promise<void> {
    if (fetching) {
      stale = true
      return
    }
    fetching = true
    try {
      do {
        stale = false
        const response = await fetch('/api/state')
        if (!response.ok) throw new Error(`GET /api/state: ${response.status}`)
        snapshot.value = (await response.json()) as Snapshot
        generation++
      } while (stale)
    } finally {
      fetching = false
    }
  }

  // A failed re-fetch leaves the last snapshot in place; the next event tries again.
  function refreshLater(): void {
    refresh().catch(() => undefined)
  }

  function loadContent(id: string): void {
    invalidate(id)
    const token = loads.get(id)
    const at = generation
    intakeApi
      .read(id)
      .then((fresh) => {
        if (loads.get(id) !== token || generation !== at) return
        const known = file(id)
        if (known) Object.assign(known, fresh)
      })
      // Deleted meanwhile (404), or offline: the next event or snapshot puts it right.
      .catch(() => undefined)
  }

  /** A file as a write by this client returned it. */
  function upsertFile(fresh: IntakeFile): void {
    if (!snapshot.value) return
    invalidate(fresh.id)
    const known = file(fresh.id)
    if (known) Object.assign(known, fresh)
    else snapshot.value.intake.files.push({ ...fresh })
  }

  function removeFile(id: string): void {
    if (!snapshot.value) return
    invalidate(id)
    echoes.delete(id)
    snapshot.value.intake.files = snapshot.value.intake.files.filter((f) => f.id !== id)
  }

  // Own saves (D-41): content this client sent whose intake.file_updated has not arrived yet.
  // The event names no sender, so a save is matched by file and size.
  const echoes = new Map<string, string[]>()

  function expectEcho(id: string, content: string): void {
    echoes.set(id, [...(echoes.get(id) ?? []), content])
  }

  function forgetEcho(id: string, content: string): void {
    const pending = echoes.get(id) ?? []
    const index = pending.indexOf(content)
    if (index >= 0) pending.splice(index, 1)
    if (!pending.length) echoes.delete(id)
  }

  function consumeEcho(id: string, size: number): string | undefined {
    const pending = echoes.get(id) ?? []
    const index = pending.findIndex((content) => utf8Size(content) === size)
    if (index < 0) return undefined
    const [content] = pending.splice(index, 1)
    if (!pending.length) echoes.delete(id)
    return content
  }

  /** Apply one intake event to the snapshot. False, before changing anything, if it cannot be applied. */
  function reduceIntake(event: LabEvent): boolean {
    const summary = event.data.file
    if (!snapshot.value || !isSummary(summary)) return false
    const fields = { id: summary.id, name: summary.name, category: summary.category, size: summary.size }
    const known = file(summary.id)
    switch (event.type) {
      case 'intake.file_created':
        if (known) {
          Object.assign(known, fields)
        } else {
          snapshot.value.intake.files.push({ ...fields, content: '' })
          if (summary.size > 0) loadContent(summary.id)
        }
        return true
      case 'intake.file_updated': {
        if (!known) return false
        const changed = Array.isArray(event.data.changed) ? event.data.changed : []
        Object.assign(known, fields)
        if (changed.includes('content')) {
          const own = consumeEcho(summary.id, summary.size)
          if (own === undefined) loadContent(summary.id)
          else known.content = own
        }
        return true
      }
      case 'intake.file_deleted':
        removeFile(summary.id)
        return true
      default:
        return false
    }
  }

  function receive(event: LabEvent): void {
    if (event.type === 'stream.resync' || !snapshot.value) {
      refreshLater()
      return
    }
    if (event.seq <= snapshot.value.seq) return
    // While a snapshot is on its way, or after a missed seq, only a new snapshot is exact.
    const next = !fetching && event.seq === snapshot.value.seq + 1
    if (next && event.type.startsWith('intake.') && reduceIntake(event)) {
      snapshot.value.seq = event.seq
      return
    }
    refreshLater()
  }

  function listen(after: number): void {
    source = new EventSource(`/api/events?after=${after}`)
    for (const type of EVENT_TYPES) {
      source.addEventListener(type, (message) => receive(JSON.parse((message as MessageEvent).data) as LabEvent))
    }
    source.onopen = () => {
      status.value = 'live'
    }
    // EventSource reconnects by itself and sends Last-Event-ID, so the server replays exactly.
    source.onerror = () => {
      status.value = 'connecting'
    }
  }

  async function connect(): Promise<void> {
    if (source || status.value === 'connecting') return
    status.value = 'connecting'
    try {
      await refresh()
    } catch {
      status.value = 'offline'
      window.setTimeout(() => {
        status.value = 'idle'
        void connect()
      }, RETRY_MS)
      return
    }
    listen(snapshot.value?.seq ?? 0)
  }

  function disconnect(): void {
    source?.close()
    source = null
    status.value = 'idle'
  }

  return {
    snapshot,
    status,
    currentIteration,
    runningBuild,
    files,
    file,
    connect,
    disconnect,
    receive,
    refresh,
    upsertFile,
    removeFile,
    expectEcho,
    forgetEcho,
  }
})
