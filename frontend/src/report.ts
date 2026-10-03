// The build report (FR-R-1, FR-R-2, D-64), as GET /api/builds/{id}/report serves it: assembled on
// the server from the completed build's kept events, so it never changes for a build id.

import { api } from './api'
import type { ChipTone } from './components/base/BaseChip.vue'

export type VerdictId = 'passed' | 'findings' | 'failed' | 'incomplete'
export type TestStatus = 'pass' | 'warn' | 'fail' | 'not_run'
export type Severity = 'high' | 'medium' | 'low' | 'advisory'
export type Category = 'Numeric' | 'Visual' | 'Latency' | 'Boundary'

export interface Verdict {
  id: VerdictId
  label: string
  tone: ChipTone
}

/** A finding (FR-T-7, D-63). Dashboard findings name panels; a boundary advisory names a file. */
export interface Finding {
  id: string
  category: Category
  test?: string
  panel?: string
  panels?: string[]
  panel_titles?: string[]
  file?: string
  line?: number
  expected: string
  shown: string
  severity: Severity
  phase: string
  message?: string
  advisory: boolean
  catalogued?: boolean
}

export interface ReportTest {
  id: string
  name: string
  phase: string
  phase_name: string
  status: TestStatus
  detail: string
  simulated: boolean
}

export interface ReportPhase {
  id: string
  index: number
  name: string
  result: string
  duration: number
  findings: string[]
}

export interface Gate {
  id: string
  kind: string
  stage: string
  resolution: string
  basis: { file: string; section: string; line: number } | null
  message: string
}

/** "Changes since iteration 1" (FR-R-3, D-69): iteration 2's report only. */
export interface Changes {
  prior_build_id: string | null
  findings: { id: string; category: Category; panel_titles: string[]; message: string; severity: Severity; status: 'resolved' | 'open' }[]
  resolved: number
  open: number
  feedback: { name: string; content: string; segments: number } | null
  updates: { file: string; section: string; segments: number[]; lines_added: number; created: boolean }[]
  kept: number[]
}

export interface Report {
  build_id: string
  iteration: number
  seed_name: string
  fingerprint: string
  verdict: Verdict
  duration: number
  counts: {
    phases: number
    phases_with_findings: number
    tests: number
    pass: number
    warn: number
    fail: number
    not_run: number
    findings: number
    advisories: number
    gates: number
  }
  phases: ReportPhase[]
  groups: { category: Category; findings: Finding[] }[]
  tests: ReportTest[]
  gates: Gate[]
  usage: { llm_calls: number; tokens_in: number; tokens_out: number; api_calls: number; sandbox_seconds: number; simulated: boolean }
  /** Null on iteration 1. Missing on a report served before M10. */
  changes?: Changes | null
}

export const reportsApi = {
  /** 404 build_not_found, 409 report_not_ready until the build completes. */
  get: (buildId: string) => api<Report>(`/api/builds/${encodeURIComponent(buildId)}/report`),
}

/** Every finding of the report that is not an advisory, in report order. */
export function dashboardFindings(report: Report): Finding[] {
  return report.groups.flatMap((group) => group.findings).filter((finding) => !finding.advisory)
}
