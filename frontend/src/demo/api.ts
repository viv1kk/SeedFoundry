// The demo controller's server actions (D-46). They keep the intake rules and emit the normal
// events, so every open page follows them.

import { api } from '../api'
import type { IntakeFile } from '../intake'

export const demoApi = {
  /** Load sample Seed. Without `replace`, a filled intake is refused with 409 intake_not_empty. */
  loadSample: (replace: boolean) => api<IntakeFile[]>('/api/demo/sample', { method: 'POST', json: { replace } }),
  clear: () => api<{ deleted: number }>('/api/demo/clear', { method: 'POST' }),
  reset: () => api<{ files_removed: number; builds_removed: number }>('/api/demo/reset', { method: 'POST' }),
}
