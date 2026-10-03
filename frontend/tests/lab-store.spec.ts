// The shell's live state (D-38): snapshot, then events after its seq; re-snapshot on newer
// events and on stream.resync, one request at a time.

import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { LabEvent } from '../src/events'
import { useLabStore } from '../src/stores/lab'
import { emptySnapshot } from './helpers'

function event(seq: number, type: LabEvent['type'] = 'intake.file_created'): LabEvent {
  return {
    seq,
    build_id: null,
    iteration: 1,
    phase: null,
    step: null,
    type,
    level: 'INFO',
    code: null,
    message: '',
    data: {},
    sim_t: null,
    wall_ts: '',
  }
}

class FakeEventSource {
  static last: FakeEventSource | null = null
  url: string
  listeners = new Map<string, (message: MessageEvent) => void>()
  onopen: (() => void) | null = null
  onerror: (() => void) | null = null
  constructor(url: string) {
    this.url = url
    FakeEventSource.last = this
  }
  addEventListener(type: string, listener: (message: MessageEvent) => void) {
    this.listeners.set(type, listener)
  }
  close() {}
}

let fetchMock: ReturnType<typeof vi.fn>

function serve(...snapshots: ReturnType<typeof emptySnapshot>[]) {
  for (const snapshot of snapshots) {
    fetchMock.mockResolvedValueOnce({ ok: true, json: async () => snapshot })
  }
}

beforeEach(() => {
  setActivePinia(createPinia())
  fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
  vi.stubGlobal('EventSource', FakeEventSource)
  FakeEventSource.last = null
})

afterEach(() => {
  vi.unstubAllGlobals()
})

const flush = () => new Promise((resolve) => setTimeout(resolve))

describe('lab store', () => {
  it('fetches the snapshot, then follows events after its seq', async () => {
    serve(emptySnapshot({ seq: 7 }))
    const lab = useLabStore()
    await lab.connect()
    expect(fetchMock).toHaveBeenCalledWith('/api/state')
    expect(lab.snapshot?.seq).toBe(7)
    expect(FakeEventSource.last?.url).toBe('/api/events?after=7')
  })

  it('listens for every event type by name', async () => {
    serve(emptySnapshot())
    const lab = useLabStore()
    await lab.connect()
    const { EVENT_TYPES } = await import('../src/events')
    expect([...(FakeEventSource.last?.listeners.keys() ?? [])].sort()).toEqual([...EVENT_TYPES].sort())
  })

  it('re-fetches the snapshot on a newer event and ignores older ones', async () => {
    serve(emptySnapshot({ seq: 3 }))
    const lab = useLabStore()
    await lab.connect()
    lab.receive(event(2))
    lab.receive(event(3))
    expect(fetchMock).toHaveBeenCalledTimes(1)
    serve(emptySnapshot({ seq: 4, builds: [{ id: 'b-1', iteration: 1, status: 'running' }] }))
    lab.receive(event(4, 'build.started'))
    await flush()
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(lab.currentIteration).toBe(1)
  })

  it('re-fetches on stream.resync whatever its seq', async () => {
    serve(emptySnapshot({ seq: 9 }), emptySnapshot({ seq: 2 }))
    const lab = useLabStore()
    await lab.connect()
    lab.receive(event(2, 'stream.resync'))
    await flush()
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(lab.snapshot?.seq).toBe(2)
  })

  it('runs one request at a time and fetches once more after a burst', async () => {
    serve(emptySnapshot({ seq: 1 }), emptySnapshot({ seq: 5 }), emptySnapshot({ seq: 5 }))
    const lab = useLabStore()
    await lab.connect()
    lab.receive(event(2))
    lab.receive(event(3))
    lab.receive(event(4))
    lab.receive(event(5))
    await flush()
    await flush()
    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(lab.snapshot?.seq).toBe(5)
  })

  it('reports offline when the server does not answer', async () => {
    vi.useFakeTimers()
    fetchMock.mockRejectedValue(new Error('down'))
    const lab = useLabStore()
    await lab.connect()
    expect(lab.status).toBe('offline')
    expect(FakeEventSource.last).toBeNull()
    vi.useRealTimers()
  })
})

// D-53: build events are applied in place, so a build's log lines, several a second, never
// re-fetch the snapshot. An event the store cannot place still does.
describe('lab store: build events (M5)', () => {
  const plan = [
    { id: 'assay', name: 'Assay', weight: 6, steps: [], tests: [] },
    { id: 'distill', name: 'Distillation', weight: 12, steps: [], tests: [] },
  ]
  const build = { id: 'b-2', iteration: 1, status: 'running' as const, seed_name: 'License Optimization', fingerprint: 'a127ba', phase: null, plan }

  function buildEvent(seq: number, type: LabEvent['type'], extra: Partial<LabEvent> = {}): LabEvent {
    return { ...event(seq, type), build_id: 'b-2', ...extra }
  }

  async function connected(seq = 10) {
    serve(emptySnapshot({ seq, builds: [{ id: 'b-1', iteration: 1, status: 'completed' }] }))
    const lab = useLabStore()
    await lab.connect()
    return lab
  }

  it('applies a whole build without fetching the snapshot again', async () => {
    const lab = await connected()
    lab.receive(buildEvent(11, 'build.started', { data: { build, replaces: ['b-1'] } }))
    expect(lab.snapshot?.builds).toEqual([build]) // the new build replaces the iteration's earlier one
    expect(lab.runningBuild?.id).toBe('b-2')
    expect(lab.snapshot?.next_build_id).toBe(3)
    lab.receive(buildEvent(12, 'phase.started', { phase: 'assay' }))
    for (let seq = 13; seq < 40; seq++) lab.receive(buildEvent(seq, seq % 2 ? 'log' : 'test.result', { phase: 'assay' }))
    lab.receive(buildEvent(40, 'phase.started', { phase: 'distill' }))
    expect(lab.build('b-2')?.phase).toBe('distill')
    lab.receive(buildEvent(41, 'build.completed'))
    await flush()
    expect(lab.build('b-2')?.status).toBe('completed')
    expect(lab.runningBuild).toBeNull()
    expect(lab.snapshot?.seq).toBe(41)
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('marks an interrupted build', async () => {
    const lab = await connected()
    lab.receive(buildEvent(11, 'build.started', { data: { build } }))
    lab.receive(buildEvent(12, 'build.interrupted', { level: 'WARN' }))
    expect(lab.build('b-2')?.status).toBe('interrupted')
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('re-fetches for a build it does not know, or after a gap', async () => {
    const lab = await connected()
    serve(emptySnapshot({ seq: 11 }), emptySnapshot({ seq: 13 }))
    lab.receive(buildEvent(11, 'log'))
    await flush()
    expect(fetchMock).toHaveBeenCalledTimes(2)
    lab.receive(buildEvent(13, 'build.started', { data: { build } }))
    await flush()
    expect(fetchMock).toHaveBeenCalledTimes(3)
  })

  it('a build returned by Start Build is added once, and never over a newer one from the stream', async () => {
    const lab = await connected()
    lab.receive(buildEvent(11, 'build.started', { data: { build } }))
    lab.receive(buildEvent(12, 'phase.started', { phase: 'assay' }))
    lab.upsertBuild({ ...build, phase: null })
    expect(lab.build('b-2')?.phase).toBe('assay')
    lab.upsertBuild({ ...build, id: 'b-3', iteration: 2 })
    expect(lab.snapshot?.builds.map((b) => b.id)).toEqual(['b-2', 'b-3'])
  })
})
