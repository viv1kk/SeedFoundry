// The demo controller's state and actions (ui-spec.md section 8, FR-DC-2, D-46, D-47).
// Load sample Seed, Clear and Reset go to the server, which emits the normal events; the
// answer is also applied here at once, so the Knowledge page changes without waiting for
// the stream. Speed lives on the server, which paces builds with it and keeps it across
// Reset; skip works while a build runs (D-48). Prefill arrives with the rebuild modal (M10):
// until then it says so in the panel's status line and does nothing else.

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { messageOf } from '../api'
import { demoApi } from '../demo/api'
import type { DemoAction } from '../demo/shortcuts'
import { toggleTheme } from '../theme'
import { useIntakeStore } from './intake'
import { useLabStore, type Build } from './lab'

export type Speed = 1 | 2 | 4

export const SPEEDS: readonly Speed[] = [1, 2, 4]

const LOCKED = 'A build is running. Knowledge files are read-only until it finishes.'
const NO_BUILD = 'No build is running, so there is nothing to skip.'
const NO_REBUILD = 'Prefill fills the rebuild modal, which arrives in M10.'

export function plural(count: number, word: string): string {
  return `${count} ${word}${count === 1 ? '' : 's'}`
}

export const useDemoStore = defineStore('demo', () => {
  const lab = useLabStore()
  const intake = useIntakeStore()

  const visible = ref(false)
  /** Build pacing (FR-DC-4: pacing only), as the server holds it. */
  const speed = ref<Speed>(1)
  /** The last action's outcome, shown in the panel. */
  const status = ref('')
  const busy = ref(false)

  /** Why an action cannot run now, or null when it can. */
  function unavailable(action: DemoAction): string | null {
    switch (action) {
      case 'sample':
      case 'clear':
        if (!lab.snapshot) return 'Knowledge files are still loading.'
        return lab.runningBuild ? LOCKED : null
      case 'start':
        if (lab.runningBuild) return 'A build is running.'
        return intake.ready ? null : `Start Build needs every core file. Missing: ${intake.missing.join(', ')}.`
      case 'skipPhase':
      case 'skipEnd':
        return lab.runningBuild ? null : NO_BUILD
      case 'prefill':
        return NO_REBUILD
      default:
        return null
    }
  }

  async function attempt(work: () => Promise<string>): Promise<boolean> {
    if (busy.value) return false
    busy.value = true
    try {
      status.value = await work()
      return true
    } catch (error) {
      status.value = messageOf(error)
      return false
    } finally {
      busy.value = false
    }
  }

  /** Load sample Seed. Without `replace`, the server refuses a filled intake (OQ-17). */
  function loadSample(replace: boolean): Promise<boolean> {
    return attempt(async () => {
      const loaded = await demoApi.loadSample(replace)
      const keep = new Set(loaded.map((file) => file.id))
      for (const file of [...lab.files]) if (!keep.has(file.id)) lab.removeFile(file.id)
      for (const file of loaded) lab.upsertFile(file)
      intake.discardMissing()
      return `Sample Seed loaded: ${plural(loaded.length, 'file')}.`
    })
  }

  function clearIntake(): Promise<boolean> {
    return attempt(async () => {
      const { deleted } = await demoApi.clear()
      for (const file of [...lab.files]) lab.removeFile(file.id)
      intake.discardMissing()
      return `Knowledge cleared: ${plural(deleted, 'file')} deleted.`
    })
  }

  function reset(): Promise<boolean> {
    return attempt(async () => {
      await demoApi.reset()
      await lab.refresh()
      intake.discardMissing()
      intake.buildNote = null
      return `Reset to start. Speed ${speed.value}x and the theme are kept.`
    })
  }

  /** Start Build, as the page's button does. Returns the build, for the caller to open its page. */
  async function startBuild(): Promise<Build | null> {
    const build = await intake.startBuild()
    status.value = build ? `Build started: iteration ${build.iteration}.` : (intake.buildNote ?? '')
    return build
  }

  /** The server's speed, which survives Reset and a page reload. */
  async function loadSpeed(): Promise<void> {
    try {
      const { speed: current } = await demoApi.speed()
      if (SPEEDS.includes(current as Speed)) speed.value = current as Speed
    } catch {
      // Offline: keep what is shown; the next change sends it.
    }
  }

  /** Shown as pressed at once, then confirmed by the server, or put back with its message. */
  async function setSpeed(next: Speed): Promise<void> {
    const before = speed.value
    speed.value = next
    status.value = `Speed ${next}x.`
    try {
      await demoApi.setSpeed(next)
    } catch (error) {
      speed.value = before
      status.value = messageOf(error)
    }
  }

  function skip(to: 'phase' | 'build'): Promise<boolean> {
    return attempt(async () => {
      const answer = await demoApi.skip(to)
      return to === 'phase' ? `Skipping to the end of ${answer.name ?? 'the phase'}.` : 'Skipping to the end of the build.'
    })
  }

  function theme(): void {
    status.value = `Theme: ${toggleTheme()}.`
  }

  return { visible, speed, status, busy, unavailable, loadSample, clearIntake, reset, startBuild, loadSpeed, setSpeed, skip, theme }
})
