// Build reports by build id (D-64, D-65). A report is assembled from a completed build's kept
// events, and a build id is never reused, so a report once loaded never changes: it is fetched
// once per build and shared by the Build page, the Review page and the dashboard frame (its
// "N findings" link and the finding highlight). A failed load is kept as a message and tried
// again the next time a page asks.

import { defineStore } from 'pinia'
import { reactive } from 'vue'
import { messageOf } from '../api'
import { reportsApi, type Report } from '../report'

export const useReportsStore = defineStore('reports', () => {
  const reports = reactive(new Map<string, Report>())
  const errors = reactive(new Map<string, string>())
  const pending = new Map<string, Promise<void>>()

  /** Load a completed build's report unless it is already held or on its way. */
  function load(buildId: string): Promise<void> {
    if (reports.has(buildId)) return Promise.resolve()
    const inFlight = pending.get(buildId)
    if (inFlight) return inFlight
    const request = reportsApi
      .get(buildId)
      .then((report) => {
        reports.set(buildId, report)
        errors.delete(buildId)
      })
      .catch((failure: unknown) => {
        errors.set(buildId, messageOf(failure))
      })
      .finally(() => pending.delete(buildId))
    pending.set(buildId, request)
    return request
  }

  return { reports, errors, load }
})
