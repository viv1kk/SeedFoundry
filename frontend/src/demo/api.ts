// The demo controller's server actions (D-46). They keep the intake rules and emit the normal
// events, so every open page follows them. Speed and skip pace the running build and emit
// nothing (D-48).

import { api } from '../api'
import type { IntakeFile } from '../intake'

export const demoApi = {
  /** Load sample Seed. Without `replace`, a filled intake is refused with 409 intake_not_empty. */
  loadSample: (replace: boolean) => api<IntakeFile[]>('/api/demo/sample', { method: 'POST', json: { replace } }),
  clear: () => api<{ deleted: number }>('/api/demo/clear', { method: 'POST' }),
  reset: () => api<{ files_removed: number; builds_removed: number }>('/api/demo/reset', { method: 'POST' }),
  speed: () => api<{ speed: number }>('/api/demo/speed'),
  setSpeed: (speed: number) => api<{ speed: number }>('/api/demo/speed', { method: 'POST', json: { speed } }),
  /** Skip to the end of the running phase or build. 409 when no build runs. */
  skip: (to: 'phase' | 'build') => api<{ skipping: string; phase?: string; name?: string }>('/api/demo/skip', { method: 'POST', json: { to } }),
}
