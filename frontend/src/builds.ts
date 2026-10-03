// Builds over /api (FR-B-1, D-49). The engine runs on the server; the client starts a build
// and follows it through the event stream.

import { api } from './api'
import type { Build } from './stores/lab'

export const buildsApi = {
  /** Start a build of the current iteration. 409 while one runs or a core file is missing. */
  start: () => api<Build>('/api/builds', { method: 'POST', json: {} }),
}
