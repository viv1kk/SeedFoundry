// The Build page's log (FR-B-4, FR-B-7, AC-7, D-54): every event of the build on screen, in
// seq order, without a gap or a double. On load or refresh it loads the build's events from
// GET /api/builds/{id}/events, and it hears the same stream as the lab store (`onEvent`), so
// lines keep arriving while the load is on its way. A build's events never change, and a build
// id is never used twice, so the log is the union of both by seq: an event already held is
// dropped, wherever it came from. A new snapshot (a gap in the seqs, a stream.resync, a server
// restart) loads the build's events again and merges them in, which fills any gap. Nothing
// here fetches the snapshot: the lab store does that, never per event.

import { defineStore } from 'pinia'
import { ref, shallowRef, triggerRef, watch } from 'vue'
import { buildsApi } from '../builds'
import type { LabEvent } from '../events'
import { useLabStore } from './lab'

export const useBuildLogStore = defineStore('buildLog', () => {
  const lab = useLabStore()

  /** The build whose events are held. */
  const buildId = ref<string | null>(null)
  /** Its events in seq order. Shallow: hundreds of events need no deep reactivity. */
  const events = shallowRef<LabEvent[]>([])
  /** True once its events have loaded at least once, so the page never shows a half log. */
  const loaded = ref(false)

  let seqs = new Set<number>()
  // The lab store's snapshot count when the latest load started: a snapshot newer than that
  // may follow events this log never heard.
  let loadedAt = -1

  /** Hold one event of the followed build. False if it is another build's or already held. */
  function add(event: LabEvent): boolean {
    if (event.build_id !== buildId.value || seqs.has(event.seq)) return false
    seqs.add(event.seq)
    const list = events.value
    if (!list.length || event.seq > list[list.length - 1].seq) list.push(event)
    else list.splice(list.findIndex((held) => held.seq > event.seq), 0, event)
    return true
  }

  lab.onEvent((event) => {
    if (add(event)) triggerRef(events)
  })

  async function load(): Promise<void> {
    const id = buildId.value
    if (!id) return
    loadedAt = lab.refreshes
    try {
      const body = await buildsApi.events(id)
      // Any answer for this build is exact up to its seq, so an older one is merged too.
      if (id !== buildId.value) return
      let changed = false
      for (const event of body.events) changed = add(event) || changed
      if (changed) triggerRef(events)
      loaded.value = true
    } catch {
      // Gone (404 after a Reset) or offline: the next snapshot says which, and loads again.
    }
  }

  /** Show this build's events, or none. Following the same build again changes nothing. */
  function follow(id: string | null): void {
    if (id === buildId.value) return
    buildId.value = id
    events.value = []
    seqs = new Set()
    loaded.value = false
    void load()
  }

  watch(
    () => lab.refreshes,
    (count) => {
      if (buildId.value && count > loadedAt) void load()
    },
  )

  return { buildId, events, loaded, follow, load }
})
