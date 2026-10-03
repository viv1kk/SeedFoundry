// Builds over /api (FR-B-1, D-49). The engine runs on the server; the client starts a build
// and follows it through the event stream.

import { api } from './api'
import type { LabEvent } from './events'
import type { Build, BuildStatus } from './stores/lab'

/** A build's events in order, as GET /api/builds/{id}/events serves them (D-49). */
export interface BuildEvents {
  build_id: string
  status: BuildStatus
  /** The server's seq when it answered: every event of the build up to it is in `events`. */
  seq: number
  events: LabEvent[]
}

export const buildsApi = {
  /** Start a build of the current iteration. 409 while one runs or a core file is missing. */
  start: () => api<Build>('/api/builds', { method: 'POST', json: {} }),
  /** The kept log of a finished build, or what a running build has emitted so far. 404 if gone. */
  events: (id: string) => api<BuildEvents>(`/api/builds/${encodeURIComponent(id)}/events`),
}
