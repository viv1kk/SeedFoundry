// The rebuild modal's state (FR-RB-1 to FR-RB-5, ui-spec.md section 6, D-70). One modal for the app,
// opened from iteration 1's report. Its feedback draft lives here, in memory only: closing the
// modal (Cancel, Escape, the close button) keeps it, so nothing typed is lost, and reopening shows
// it; a page reload or a successful Start Rebuild clears it. The view (Feedback, Feedback + Report,
// Feedback + Dashboard) and the embedded dashboard's drill path live here too, never in the URL,
// so the page behind the modal does not move. Start Rebuild is one request that saves the
// feedback and starts iteration 2 (D-67).

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { messageOf } from '../api'
import { buildsApi } from '../builds'
import { demoApi } from '../demo/api'
import { useLabStore, type Build } from './lab'

export const FEEDBACK_NAME = 'observer-feedback-iteration-1.md'

export type RebuildView = 'feedback' | 'report' | 'dashboard'

export const useRebuildStore = defineStore('rebuild', () => {
  const lab = useLabStore()

  const open = ref(false)
  /** The iteration 1 build the feedback is about. */
  const buildId = ref<string | null>(null)
  const draft = ref('')
  const view = ref<RebuildView>('feedback')
  /** The embedded dashboard's drill path, held off the URL. */
  const drill = ref('')
  /** A finding chosen in the embedded report, outlined in the embedded dashboard. */
  const finding = ref<string | null>(null)
  const busy = ref(false)
  const error = ref('')

  const build = computed(() => lab.build(buildId.value))
  const empty = computed(() => !draft.value.trim())

  /**
   * Why Rebuild is not offered for a build, or null when it is: iteration 1 only (D-6), completed,
   * while the Seed is still on iteration 1 and not approved, with no build running (D-67).
   */
  function unavailable(candidate: Build): string | null {
    const snapshot = lab.snapshot
    if (candidate.iteration !== 1 || candidate.status !== 'completed') return 'Rebuild is offered on a completed iteration 1 only.'
    if (!snapshot) return 'The lab is still loading.'
    if (snapshot.approval) return 'This Seed is approved, so it is not rebuilt.'
    if (snapshot.iteration !== 1 || snapshot.builds.some((b) => b.iteration === 2)) return 'Iteration 2 was rebuilt from this report.'
    if (lab.runningBuild) return 'A build is running.'
    return null
  }

  function show(from: Build): void {
    if (unavailable(from)) return
    buildId.value = from.id
    error.value = ''
    // A feedback file made by hand on Knowledge is where the draft starts; Start Rebuild rewrites it.
    if (!draft.value.trim()) {
      const saved = lab.files.find((f) => f.category === 'misc_context' && f.name === FEEDBACK_NAME)
      if (saved) draft.value = saved.content
    }
    open.value = true
  }

  function close(): void {
    open.value = false
    error.value = ''
  }

  function setView(next: RebuildView): void {
    view.value = next
    if (next !== 'dashboard') finding.value = null
  }

  /** A finding in the embedded report: shown on the embedded dashboard at All products. */
  function showFinding(id: string): void {
    finding.value = id
    drill.value = ''
    view.value = 'dashboard'
  }

  function navigate(path: string): void {
    drill.value = path
    finding.value = null
  }

  /** Prefill (Shift+F, FR-DC-2): the demo's feedback, from the server. Replaces the draft. */
  async function prefill(): Promise<string> {
    const { content } = await demoApi.feedback()
    draft.value = content
    return 'Feedback prefilled with the demo text.'
  }

  /** Start Rebuild. Returns the new build, or null with the server's reason in `error`. */
  async function start(): Promise<Build | null> {
    if (empty.value || busy.value) return null
    busy.value = true
    error.value = ''
    try {
      const started = await buildsApi.rebuild(draft.value)
      lab.upsertBuild(started)
      draft.value = ''
      drill.value = ''
      finding.value = null
      view.value = 'feedback'
      open.value = false
      return started
    } catch (failure) {
      error.value = messageOf(failure)
      return null
    } finally {
      busy.value = false
    }
  }

  return { open, buildId, build, draft, view, drill, finding, busy, error, empty, unavailable, show, close, setView, showFinding, navigate, prefill, start }
})
