// The rebuild modal's state (FR-RB-1 to FR-RB-5, ui-spec.md section 6, D-70). One modal for the app,
// opened by Reject on the current iteration's report, whatever its verdict (D-81). Its feedback draft lives here, in memory only: closing the
// modal (Cancel, Escape, the close button) keeps it, so nothing typed is lost, and reopening shows
// it; a page reload or a successful Start Rebuild clears it. The view (Feedback, Feedback + Report,
// Feedback + Dashboard) and the embedded dashboard's drill path live here too, never in the URL,
// so the page behind the modal does not move. Start Rebuild is one request that saves the
// feedback as observer-feedback-iteration-<n>.md and starts iteration n + 1 (D-67, D-81).

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { messageOf } from '../api'
import { buildsApi } from '../builds'
import { demoApi } from '../demo/api'
import { useLabStore, type Build } from './lab'

/** The feedback file of the iteration it rejects (D-81). */
export function feedbackName(rejected: number): string {
  return `observer-feedback-iteration-${rejected}.md`
}

export const FEEDBACK_NAME = feedbackName(1)

export type RebuildView = 'feedback' | 'report' | 'dashboard'

/** What a superseded report says: the next iteration was rebuilt from it. */
export function rebuiltFrom(build: Build): string {
  return `Iteration ${build.iteration + 1} was rebuilt from this report.`
}

export const useRebuildStore = defineStore('rebuild', () => {
  const lab = useLabStore()

  const open = ref(false)
  /** The build the feedback rejects. */
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
  /** The iteration the open modal rejects, and its feedback file. */
  const rejected = computed(() => build.value?.iteration ?? 1)
  const name = computed(() => feedbackName(rejected.value))

  /**
   * Why Reject is not offered for a build, or null when it is (D-81): the current iteration's
   * completed build, passed or not, while the Seed is not approved, with no build running (D-67).
   */
  function unavailable(candidate: Build): string | null {
    const snapshot = lab.snapshot
    if (candidate.status !== 'completed') return 'Reject is offered on a completed build only.'
    if (!snapshot) return 'The lab is still loading.'
    if (snapshot.approval) return 'This Seed is approved, so it is not rebuilt.'
    if (snapshot.iteration !== candidate.iteration || snapshot.builds.some((b) => b.iteration > candidate.iteration)) {
      return rebuiltFrom(candidate)
    }
    if (lab.runningBuild) return 'A build is running.'
    return null
  }

  function show(from: Build): void {
    if (unavailable(from)) return
    // A draft kept from another iteration's modal is not this one's feedback.
    if (buildId.value !== from.id) draft.value = ''
    buildId.value = from.id
    error.value = ''
    // A feedback file made by hand on Knowledge is where the draft starts; Start Rebuild rewrites it.
    if (!draft.value.trim()) {
      const saved = lab.files.find((f) => f.category === 'misc_context' && f.name === feedbackName(from.iteration))
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

  /** Prefill (Shift+F, FR-DC-2): the demo's feedback on this iteration, from the server. Replaces the draft. */
  async function prefill(): Promise<string> {
    const { content } = await demoApi.feedback(rejected.value)
    draft.value = content
    return 'Feedback prefilled with the demo text.'
  }

  /** Start Rebuild. Returns the new build, or null with the server's reason in `error`. */
  async function start(): Promise<Build | null> {
    if (empty.value || busy.value) return null
    busy.value = true
    error.value = ''
    try {
      const started = await buildsApi.rebuild(rejected.value, draft.value)
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

  return { open, buildId, build, rejected, name, draft, view, drill, finding, busy, error, empty, unavailable, show, close, setView, showFinding, navigate, prefill, start }
})
