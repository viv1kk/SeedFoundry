// Event types the frontend listens for on GET /api/events. SSE frames are named by type,
// so a type missing here is never heard. tests/events-contract.spec.ts checks this list
// against backend/seedfoundry/events.py EVENT_TYPES.

/** Build events (build-simulation.md section 3), as backend BUILD_EVENT_TYPES. */
export const BUILD_EVENT_TYPES = [
  'build.started',
  'phase.started',
  'step.started',
  'log',
  'llm.call',
  'api.call',
  'test.result',
  'gate.auto_resolved',
  'finding.raised',
  'step.completed',
  'phase.completed',
  'build.completed',
  'report.ready',
  'build.interrupted',
] as const

export const EVENT_TYPES = [
  ...BUILD_EVENT_TYPES,
  // intake (D-32)
  'intake.file_created',
  'intake.file_updated',
  'intake.file_deleted',
  // demo controller (D-46)
  'demo.reset',
  // stream (D-31)
  'stream.resync',
] as const

export type EventType = (typeof EVENT_TYPES)[number]

export type Level = 'INFO' | 'LLM' | 'API' | 'TEST' | 'PASS' | 'WARN' | 'FAIL'

/** One event, as backend Event serialises it. */
export interface LabEvent {
  seq: number
  build_id: string | null
  iteration: number
  phase: string | null
  step: string | null
  type: EventType
  level: Level
  code: string | null
  message: string
  data: Record<string, unknown>
  sim_t: number | null
  wall_ts: string
}
