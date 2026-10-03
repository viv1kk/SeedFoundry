// The Build page's derivations (FR-B-3, FR-B-4, D-54): phase and sub-step states from events,
// iteration 2's feedback group, an interrupted build, times from sim_t, console lines and filter.

import { describe, expect, it } from 'vitest'
import { clock, consoleLines, derivePhases, duration, elapsed, filterLines, progress, stamp } from '../src/stepper'
import { buildRecord, expectedLines, script } from './build-script'

const upTo = (events: ReturnType<typeof script>, predicate: (e: (typeof events)[number]) => boolean) =>
  events.slice(0, events.findIndex(predicate) + 1)

describe('phases and sub-steps from events (FR-B-3)', () => {
  it('shows every phase of the plan as pending before any event', () => {
    const phases = derivePhases(buildRecord(), [])
    expect(phases.map((p) => [p.index, p.name, p.state])).toEqual(
      ['Assay', 'Distillation', 'Synthesis', 'Cross-Examination', 'Germination Trial', 'Containment', 'Planting', 'Seeding & Life', 'Stress & Probe', 'Harvest Validation', 'Teardown & Report'].map(
        (name, i) => [i + 1, name, 'pending'],
      ),
    )
  })

  it('marks the running phase active, and its sub-steps done, active and pending', () => {
    const events = upTo(script(), (e) => e.type === 'step.started' && e.step === 'contain.sandbox')
    const phases = derivePhases(buildRecord({ phase: 'contain' }), events)
    expect(phases.map((p) => p.state)).toEqual([...Array(5).fill('done'), 'active', ...Array(5).fill('pending')])
    const contain = phases[5]
    expect(contain.steps.map((s) => [s.name, s.state, s.summary])).toEqual([
      ['Seed API handshake', 'done', 'seed api handshake done'],
      ['Provision isolated sandbox', 'active', null],
      ['Upload seed files', 'pending', null],
      ['Verify upload checksums', 'pending', null],
    ])
  })

  it('gives each done phase its result, test counts and simulated duration', () => {
    const events = script({ results: { germ: 'incomplete', probe: 'findings', harvest: 'failed' } })
    const phases = derivePhases(buildRecord({ status: 'completed' }), events)
    expect(phases.map((p) => p.result)).toEqual(['passed', 'passed', 'passed', 'passed', 'incomplete', 'passed', 'passed', 'passed', 'findings', 'failed', 'passed'])
    expect(phases[4]).toMatchObject({ tests: 2, notRun: 2 })
    expect(phases[8].findings).toBe(1) // the advisory beside N-1 is not counted (D-12)
    expect(phases[9].failedTests).toEqual(['T-16', 'T-17', 'T-18', 'T-19', 'T-20'])
    expect(phases[0].duration).toBeCloseTo(4.5) // Assay: weight 6 of 100 over 75 s
    expect(phases[7].duration).toBeCloseTo(12)
    expect(phases.every((p) => p.state === 'done' && p.steps.every((s) => s.state === 'done'))).toBe(true)
  })

  it("groups iteration 2's five feedback sub-steps first in Assay (FR-RB-8)", () => {
    const build = buildRecord({ id: 'b-2', iteration: 2 })
    const events = upTo(script({ build }), (e) => e.type === 'step.started' && e.step === 'assay.feedback-environment')
    const assay = derivePhases(build, events)[0]
    expect(assay.steps.filter((s) => s.feedback).map((s) => [s.name, s.state, s.summary])).toEqual([
      // D-71: the real routing's summaries (D-68), where D-52's stub said "no change".
      ['Route feedback to Ensemble files', 'done', '9 of 10 segments to 4 files'],
      ['Update person.md', 'done', '+4 lines in Reasoning methods'],
      ['Update instrument-awareness.md', 'done', '+4 lines in Model Behaviour'],
      ['Update environment.md', 'active', null],
      ['Update music.md', 'pending', null],
    ])
    expect(assay.steps.slice(0, 5).every((s) => s.feedback)).toBe(true)
    expect(derivePhases(buildRecord(), [])[0].steps.some((s) => s.feedback)).toBe(false)
  })

  it('an interrupted build: the phase it was in stopped; earlier phases whose events were lost ran', () => {
    const live = upTo(script(), (e) => e.type === 'step.started' && e.step === 'contain.upload')
    const stopped = derivePhases(buildRecord({ status: 'interrupted', phase: 'contain' }), live)
    expect(stopped.map((p) => p.state)).toEqual([...Array(5).fill('done'), 'stopped', ...Array(5).fill('pending')])
    expect(stopped[5].steps.map((s) => s.state)).toEqual(['done', 'done', 'stopped', 'pending'])
    // After a restart the server kept none of its events (D-49): only build.interrupted.
    const lost = derivePhases(buildRecord({ status: 'interrupted', phase: 'contain' }), [])
    expect(lost.map((p) => [p.state, p.result])).toEqual([...Array(5).fill(['done', null]), ['stopped', null], ...Array(5).fill(['pending', null])])
  })
})

describe('times from sim_t (FR-DC-4)', () => {
  it('formats the header clock, log stamps and durations, never rounding a stamp up', () => {
    expect(clock(0)).toBe('00:00')
    expect(clock(75)).toBe('01:15')
    expect(clock(59.99)).toBe('00:59')
    expect([0, 0.45, 3.6, 4.05, 64.2, 74.182, 75].map(stamp)).toEqual(['00:00.0', '00:00.4', '00:03.6', '00:04.0', '01:04.2', '01:14.1', '01:15.0'])
    expect(stamp(null)).toBe('--:--.-')
    expect(duration(4.5)).toBe('4.5 s')
    expect(duration(12)).toBe('12.0 s')
  })

  it('elapsed is the latest sim_t; progress is sim_t over the build length', () => {
    const events = upTo(script(), (e) => e.type === 'phase.started' && e.phase === 'seeding')
    expect(elapsed(events)).toBeCloseTo(44.25) // phases 1 to 7 weigh 59 of 100
    const build = buildRecord()
    expect(progress(build, derivePhases(build, events), elapsed(events))).toBeCloseTo(0.59)
    expect(progress({ ...build, status: 'completed' }, [], 0)).toBe(1)
    // A record saved before M6 has no length: the finished phases' weight stands in.
    const old = { ...build, sim_seconds: 0 }
    expect(progress(old, derivePhases(old, events), elapsed(events))).toBeCloseTo(0.59)
  })
})

describe('console lines (FR-B-4, build-simulation.md section 4)', () => {
  it('is one line per event except step.started and step.completed, in order', () => {
    const events = script()
    const lines = consoleLines(events)
    expect(lines.map((l) => l.seq)).toEqual(expectedLines(events))
    expect(lines[0]).toEqual({ seq: 1, time: '00:00.0', level: 'INFO', message: 'Build started: iteration 1, seed "License Optimization"' })
    expect(lines.at(-1)).toMatchObject({ time: '01:15.0', message: expect.stringMatching(/^Build completed/) })
  })

  it('filters by level: TEST includes PASS, INFO shows only under All', () => {
    const lines = consoleLines(script({ results: { germ: 'incomplete', probe: 'findings', harvest: 'failed' } }))
    const levels = (filter: Parameters<typeof filterLines>[1]) => [...new Set(filterLines(lines, filter).map((l) => l.level))].sort()
    expect(levels('all')).toEqual(['API', 'FAIL', 'INFO', 'LLM', 'PASS', 'TEST', 'WARN'])
    expect(levels('LLM')).toEqual(['LLM'])
    expect(levels('API')).toEqual(['API'])
    expect(levels('TEST')).toEqual(['PASS', 'TEST'])
    expect(levels('WARN')).toEqual(['WARN'])
    expect(levels('FAIL')).toEqual(['FAIL'])
  })
})
