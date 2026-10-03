// Live server state for the shell (D-38): GET /api/state, then GET /api/events after its seq.
// M2 has no reducers: any newer event re-fetches the snapshot, one request at a time.
// Later milestones add reducers for the events they render (intake in M3, build in M5 and M6).

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { EVENT_TYPES, type LabEvent } from '../events'

export type BuildStatus = 'running' | 'completed' | 'interrupted'

export interface Build {
  id: string
  iteration: number
  status: BuildStatus
}

export interface IntakeFile {
  id: string
  name: string
  category: string
  content: string
  size: number
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

export const useLabStore = defineStore('lab', () => {
  const snapshot = ref<Snapshot | null>(null)
  const status = ref<'idle' | 'connecting' | 'live' | 'offline'>('idle')

  /** The iteration of the latest build, or null before the first build. */
  const currentIteration = computed(() => {
    const builds = snapshot.value?.builds ?? []
    return builds.length ? builds[builds.length - 1].iteration : null
  })

  let source: EventSource | null = null
  let fetching = false
  let stale = false

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
      } while (stale)
    } finally {
      fetching = false
    }
  }

  // A failed re-fetch leaves the last snapshot in place; the next event tries again.
  function refreshLater(): void {
    refresh().catch(() => undefined)
  }

  function receive(event: LabEvent): void {
    if (event.type === 'stream.resync') {
      refreshLater()
      return
    }
    if (snapshot.value && event.seq <= snapshot.value.seq) return
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

  return { snapshot, status, currentIteration, connect, disconnect, receive, refresh }
})
