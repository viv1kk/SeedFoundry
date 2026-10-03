// Contract: every event type the backend can emit is known to the frontend, which listens
// for SSE frames by type (M1 notes, D-38). Read from backend/seedfoundry/events.py.

import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { BUILD_EVENT_TYPES, EVENT_TYPES } from '../src/events'

const SOURCE = readFileSync(resolve(__dirname, '..', '..', 'backend', 'seedfoundry', 'events.py'), 'utf8')

function tuple(name: string): string[] {
  const body = SOURCE.match(new RegExp(`^${name} = \\(([\\s\\S]*?)\\)`, 'm'))?.[1]
  if (body === undefined) throw new Error(`${name} not found in events.py`)
  return [...body.matchAll(/"([^"]+)"/g)].map((m) => m[1])
}

function backendEventTypes(): string[] {
  const composition = SOURCE.match(/^EVENT_TYPES = (.+)$/m)?.[1]
  if (!composition) throw new Error('EVENT_TYPES not found in events.py')
  return composition.split('+').flatMap((part) => tuple(part.trim()))
}

describe('event type contract', () => {
  const backend = backendEventTypes()

  it('reads the backend list', () => {
    expect(backend.length).toBeGreaterThan(0)
    expect(backend).toContain('stream.resync')
  })

  it('every backend EVENT_TYPES entry is known to the frontend', () => {
    const known = new Set<string>(EVENT_TYPES)
    expect(backend.filter((type) => !known.has(type))).toEqual([])
  })

  it('the build types the lab store reduces are the backend build types (M5)', () => {
    expect([...BUILD_EVENT_TYPES]).toEqual(tuple('BUILD_EVENT_TYPES'))
  })

  it('the frontend lists no type the backend cannot emit', () => {
    const emitted = new Set(backend)
    expect(EVENT_TYPES.filter((type) => !emitted.has(type))).toEqual([])
  })
})
