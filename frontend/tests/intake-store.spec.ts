// Intake state (D-41): events applied in place, content fetched only for changes this client
// did not make, drafts that no event can overwrite, and autosave (FR-IN-6).

import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { LabEvent } from '../src/events'
import { AUTOSAVE_MS, useIntakeStore } from '../src/stores/intake'
import { useLabStore } from '../src/stores/lab'
import { FakeServer } from './fake-server'

let server: FakeServer

function event(seq: number, type: LabEvent['type'], data: Record<string, unknown>): LabEvent {
  return { seq, build_id: null, iteration: 1, phase: null, step: null, type, level: 'INFO', code: null, message: '', data, sim_t: null, wall_ts: '' }
}

function summary(id: string, name: string, category: string, content: string) {
  return { id, name, category, size: new TextEncoder().encode(content).length }
}

const flush = () => new Promise((resolve) => setTimeout(resolve))

function stores() {
  const lab = useLabStore()
  lab.snapshot = server.snapshot()
  const intake = useIntakeStore()
  return { lab, intake }
}

beforeEach(async () => {
  setActivePinia(createPinia())
  server = new FakeServer([{ name: 'music.md', category: 'music', content: 'old' }])
  server.seq = 1
  vi.stubGlobal('fetch', server.fetch)
})

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

describe('intake events in the lab store (D-41)', () => {
  it('applies a created event in place and fetches the new content', async () => {
    const { lab } = stores()
    server.add('person.md', 'person', 'who')
    lab.receive(event(2, 'intake.file_created', { file: summary('f-2', 'person.md', 'person', 'who'), source: 'import' }))
    expect(lab.snapshot?.seq).toBe(2)
    expect(lab.file('f-2')?.name).toBe('person.md')
    await flush()
    expect(lab.file('f-2')?.content).toBe('who')
    expect(server.calls.map((c) => `${c.method} ${c.path}`)).toEqual(['GET /api/intake/files/f-2'])
  })

  it('does not fetch an empty new file', async () => {
    const { lab } = stores()
    lab.receive(event(2, 'intake.file_created', { file: summary('f-2', 'notes.md', 'misc_context', ''), source: 'new' }))
    await flush()
    expect(lab.file('f-2')?.content).toBe('')
    expect(server.calls).toEqual([])
  })

  it('applies a rename or category change without fetching', async () => {
    const { lab } = stores()
    lab.receive(event(2, 'intake.file_updated', { file: summary('f-1', 'tune.md', 'misc_context', 'old'), changed: ['name', 'category'] }))
    await flush()
    expect(lab.file('f-1')).toMatchObject({ name: 'tune.md', category: 'misc_context', content: 'old' })
    expect(server.calls).toEqual([])
  })

  it("fetches content changed elsewhere, since events carry none (D-32)", async () => {
    const { lab } = stores()
    server.files[0].content = 'from another tab'
    lab.receive(event(2, 'intake.file_updated', { file: summary('f-1', 'music.md', 'music', 'from another tab'), changed: ['content'] }))
    await flush()
    expect(lab.file('f-1')?.content).toBe('from another tab')
    expect(server.calls.map((c) => `${c.method} ${c.path}`)).toEqual(['GET /api/intake/files/f-1'])
  })

  it('removes a deleted file', () => {
    const { lab } = stores()
    lab.receive(event(2, 'intake.file_deleted', { file: summary('f-1', 'music.md', 'music', 'old') }))
    expect(lab.files).toEqual([])
    expect(lab.snapshot?.seq).toBe(2)
  })

  it('re-fetches the snapshot after a gap in seqs', async () => {
    const { lab } = stores()
    server.seq = 5
    lab.receive(event(3, 'intake.file_deleted', { file: summary('f-1', 'music.md', 'music', 'old') }))
    await flush()
    expect(server.calls.map((c) => c.path)).toEqual(['/api/state'])
    expect(lab.snapshot?.seq).toBe(5)
    expect(lab.files).toHaveLength(1)
  })

  it('re-fetches the snapshot for an update to a file it does not know', async () => {
    const { lab } = stores()
    lab.receive(event(2, 'intake.file_updated', { file: summary('f-9', 'x.md', 'misc_context', 'x'), changed: ['content'] }))
    await flush()
    expect(server.calls.map((c) => c.path)).toEqual(['/api/state'])
  })
})

describe('FR-IN-6: autosave and the echo of an own save (D-41)', () => {
  it('saves after a short pause, with the file dirty until the server has it', async () => {
    vi.useFakeTimers()
    const { intake } = stores()
    intake.edit('f-1', 'new text')
    expect(intake.isDirty('f-1')).toBe(true)
    await vi.advanceTimersByTimeAsync(AUTOSAVE_MS - 100)
    expect(server.writes()).toEqual([])
    await vi.advanceTimersByTimeAsync(100)
    expect(server.writes().map((c) => [c.method, c.path, c.body])).toEqual([['PATCH', '/api/intake/files/f-1', { content: 'new text' }]])
    expect(intake.isDirty('f-1')).toBe(false)
    expect(intake.text('f-1')).toBe('new text')
  })

  it('waits for typing to stop before saving', async () => {
    vi.useFakeTimers()
    const { intake } = stores()
    for (const text of ['a', 'ab', 'abc']) {
      intake.edit('f-1', text)
      await vi.advanceTimersByTimeAsync(AUTOSAVE_MS / 2)
    }
    expect(server.writes()).toEqual([])
    await vi.advanceTimersByTimeAsync(AUTOSAVE_MS)
    expect(server.writes().map((c) => c.body)).toEqual([{ content: 'abc' }])
  })

  it('saves at once on flush, as on a file switch', async () => {
    const { intake } = stores()
    intake.edit('f-1', 'switching away')
    await intake.flush('f-1')
    expect(server.writes().map((c) => c.body)).toEqual([{ content: 'switching away' }])
  })

  it('does not save text that matches the server again', async () => {
    const { intake } = stores()
    intake.edit('f-1', 'olde')
    intake.edit('f-1', 'old')
    expect(intake.isDirty('f-1')).toBe(false)
    await intake.flush('f-1')
    expect(server.writes()).toEqual([])
  })

  it('takes the echo of its own save without fetching, and keeps text typed since', async () => {
    const { lab, intake } = stores()
    server.holdWrites = true
    intake.edit('f-1', 'first')
    const saving = intake.flush('f-1')
    await flush()
    intake.edit('f-1', 'first, then more')
    // The server applies the save and its event arrives before the PATCH answer.
    server.release()
    lab.receive(event(2, 'intake.file_updated', { file: summary('f-1', 'music.md', 'music', 'first'), changed: ['content'] }))
    await saving
    expect(server.calls.filter((c) => c.method === 'GET')).toEqual([])
    expect(lab.file('f-1')?.content).toBe('first')
    expect(intake.text('f-1')).toBe('first, then more')
    expect(intake.isDirty('f-1')).toBe(true)
  })

  it('a change from elsewhere does not overwrite unsaved text', async () => {
    const { lab, intake } = stores()
    intake.edit('f-1', 'mine')
    server.files[0].content = 'theirs'
    lab.receive(event(2, 'intake.file_updated', { file: summary('f-1', 'music.md', 'music', 'theirs'), changed: ['content'] }))
    await flush()
    expect(lab.file('f-1')?.content).toBe('theirs')
    expect(intake.text('f-1')).toBe('mine')
  })

  it('a clean file follows changes from elsewhere', async () => {
    const { lab, intake } = stores()
    server.files[0].content = 'theirs'
    lab.receive(event(2, 'intake.file_updated', { file: summary('f-1', 'music.md', 'music', 'theirs'), changed: ['content'] }))
    await flush()
    expect(intake.text('f-1')).toBe('theirs')
  })

  it('FR-IN-11: a refused save keeps the draft and shows the server message', async () => {
    const { intake } = stores()
    server.refuseNext((c) => c.method === 'PATCH', 413, 'file_too_large', 'music.md is 1,048,577 bytes. Files are limited to 1 MB (1,048,576 bytes).')
    intake.edit('f-1', 'x'.repeat(10))
    await intake.flush('f-1')
    expect(intake.saveError('f-1')).toBe('music.md is 1,048,577 bytes. Files are limited to 1 MB (1,048,576 bytes).')
    expect(intake.isDirty('f-1')).toBe(true)
  })

  it('FR-B-8: a save refused with intake_locked is kept and sent once the build is over', async () => {
    const { lab, intake } = stores()
    server.builds = [{ id: 'b-1', iteration: 1, status: 'running' }]
    lab.snapshot!.builds = [{ id: 'b-1', iteration: 1, status: 'running' }]
    intake.edit('f-1', 'typed before the build')
    await intake.flush('f-1')
    expect(intake.saveError('f-1')).toBe('Knowledge files are read-only while a build runs.')
    expect(intake.isDirty('f-1')).toBe(true)
    server.builds = []
    lab.snapshot!.builds = [{ id: 'b-1', iteration: 1, status: 'completed' }]
    await flush()
    await flush()
    expect(server.files[0].content).toBe('typed before the build')
    expect(intake.saveError('f-1')).toBeNull()
    expect(intake.isDirty('f-1')).toBe(false)
  })
})

describe('FR-IN-8: core checklist', () => {
  it('a slot is complete when its file is non-empty; whitespace only does not count (D-42)', async () => {
    const { lab, intake } = stores()
    await intake.loadCategories()
    const complete = () => Object.fromEntries(intake.coreSlots.map((s) => [s.category.id, s.complete]))
    expect(complete()).toEqual({ person: false, instrument_awareness: false, environment: false, music: true })
    intake.edit('f-1', '  \n\t ')
    expect(complete().music).toBe(false)
    intake.edit('f-1', 'x')
    expect(complete().music).toBe(true)
    lab.snapshot!.intake.files.push({ id: 'f-2', name: 'person.md', category: 'person', content: '\n\n', size: 2 })
    expect(complete().person).toBe(false)
    expect(intake.missing).toEqual(['Identity.md', 'Tools_and_Skills.md', 'Environment.md'])
  })
})
