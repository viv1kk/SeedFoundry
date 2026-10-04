// The approved Seed (FR-F-1, FR-R-4, D-73, D-75). Approve on a report records the approval on the
// server and returns the Seed page's data, which is kept here so the Seed page opens without a
// second request; the snapshot's `approval` is set at once too, so the journey indicator and the
// reports follow before the `seed.approved` event's snapshot arrives. The page data is loaded again
// whenever the approval names another build, and dropped when Reset clears it.

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ApiError, messageOf } from '../api'
import { seedApi, type SeedPackage } from '../seed'
import { useLabStore, type Build } from './lab'

export const useSeedStore = defineStore('seed', () => {
  const lab = useLabStore()

  const seed = ref<SeedPackage | null>(null)
  /** Why the page data could not be loaded; empty when there is simply no approved Seed. */
  const error = ref('')
  const loading = ref(false)
  const approving = ref(false)

  /**
   * Why a build cannot be approved now, or null when it can (D-73): a completed build of the current
   * iteration, once, with no build running. Iteration 1 is not approved once iteration 2 has started.
   */
  function unavailable(build: Build): string | null {
    const snapshot = lab.snapshot
    if (!snapshot) return 'The lab is still loading.'
    if (snapshot.approval) return `This Seed is already approved at iteration ${snapshot.approval.iteration}.`
    if (build.status !== 'completed') return 'Approve is offered on a completed build only.'
    if (lab.runningBuild) return 'A build is running. Approve once it has finished.'
    if (build.iteration !== snapshot.iteration) return 'Iteration 2 was rebuilt from this report, so iteration 2 is the one to approve.'
    return null
  }

  /** The approved Seed's page data, or null before approval (404 seed_not_approved). */
  async function load(): Promise<void> {
    loading.value = true
    error.value = ''
    try {
      seed.value = await seedApi.get()
    } catch (failure) {
      seed.value = null
      if (!(failure instanceof ApiError && failure.code === 'seed_not_approved')) error.value = messageOf(failure)
    } finally {
      loading.value = false
    }
  }

  function clear(): void {
    seed.value = null
    error.value = ''
  }

  /** Approve a build. Returns null when approved, else the server's reason. */
  async function approve(build: Build): Promise<string | null> {
    if (approving.value) return null
    approving.value = true
    try {
      const approved = await seedApi.approve(build.id)
      seed.value = approved
      error.value = ''
      if (lab.snapshot) lab.snapshot.approval = { ...approved.approval }
      return null
    } catch (failure) {
      return messageOf(failure)
    } finally {
      approving.value = false
    }
  }

  return { seed, error, loading, approving, unavailable, load, clear, approve }
})
