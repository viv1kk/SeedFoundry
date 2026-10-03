// The build route until M6 (OQ-18, D-53): the placeholder with one line saying what the
// iteration's build is doing, kept current from build events.

import { afterEach, describe, expect, it } from 'vitest'
import type { LabEvent } from '../src/events'
import { useLabStore, type Build } from '../src/stores/lab'
import { emptySnapshot, mountApp } from './helpers'

afterEach(() => {
  document.body.innerHTML = ''
})

const plan = ['Assay', 'Distillation', 'Synthesis'].map((name, i) => ({ id: `p${i + 1}`, name, weight: 1, steps: [], tests: [] }))

function build(overrides: Partial<Build> = {}): Build {
  return { id: 'b-1', iteration: 1, status: 'running', seed_name: 'License Optimization', phase: 'p1', plan, ...overrides }
}

async function note(builds: Build[], path = '/build/1') {
  const { wrapper } = await mountApp(path, emptySnapshot({ seq: 5, builds }))
  return { wrapper, text: () => wrapper.find('main [data-test="placeholder"] p').text() }
}

describe('build route until M6', () => {
  it('says which phase is running, and follows phase.started', async () => {
    const { wrapper, text } = await note([build()])
    expect(wrapper.find('main h1').text()).toBe('Build, iteration 1')
    expect(text()).toBe('Build running: phase 1 of 3, Assay. The phase stepper and console arrive in M6.')
    const lab = useLabStore()
    lab.receive({ seq: 6, build_id: 'b-1', iteration: 1, phase: 'p3', step: null, type: 'phase.started', level: 'INFO', code: null, message: '', data: {}, sim_t: 1, wall_ts: '' } as LabEvent)
    await wrapper.vm.$nextTick()
    expect(text()).toBe('Build running: phase 3 of 3, Synthesis. The phase stepper and console arrive in M6.')
  })

  it.each([
    [build({ status: 'completed' }), 'Build completed. The phase stepper and console arrive in M6. The report arrives in M9.'],
    [build({ status: 'interrupted' }), 'This build stopped before it finished. Start it again from Knowledge. The phase stepper and console arrive in M6.'],
    [build({ iteration: 2, id: 'b-2' }), 'No build for this iteration yet. The phase stepper and console arrive in M6.'],
  ])('says what the build is: %#', async (shown, expected) => {
    const { text } = await note([shown])
    expect(text()).toBe(expected)
  })
})
