// The approved Seed (FR-F-1 to FR-F-5, ui-spec.md section 7, D-73 to D-75), as GET /api/seed serves
// it: assembled on the server from the approved build's kept files and log, so the same approval
// always gives the same data. Only `approval.approved_at` follows the clock; the page shows its date.
// Downloads are plain links to relative /api URLs, so the browser saves what the server sends and
// nothing leaves localhost (NFR-2, D-38).

import { api } from './api'
import type { Category, Severity, TestStatus, Verdict } from './report'

export interface SeedFile {
  name: string
  title: string
  description: string
  bytes: number
  sha256: string
  content: string
  url: string
}

export interface SeedPhase {
  id: string
  index: number
  name: string
  result: 'passed' | 'findings' | 'incomplete' | 'failed'
  findings: string[]
  tests: { id: string; name: string; status: TestStatus }[]
}

export type HistoryItem =
  | {
      kind: 'iteration'
      iteration: number
      build_id: string
      verdict: Verdict
      findings: number
      approved: boolean
      resolved?: number
      open?: number
      prior_findings?: number
    }
  /** The observer feedback that rejected iteration `rejected` (missing before D-81: iteration 1). */
  | { kind: 'feedback'; rejected?: number; name: string; content: string; segments: number; routed: number; files_updated: number }

export interface KnownIssue {
  id: string
  category: Category
  severity: Severity
  panel_titles: string[]
  message: string
  expected: string
  shown: string
}

export interface SeedPackage {
  seed_name: string
  fingerprint: string
  approval: { iteration: number; build_id: string; approved_at: string | null }
  purpose: { from: 'purpose' | 'first_paragraph' | 'none'; text: string }
  verdict: Verdict
  counts: { tests: number; pass: number; warn: number; fail: number; not_run: number; findings: number; phases: number; phases_with_findings: number }
  phases: SeedPhase[]
  history: HistoryItem[]
  known_issues: KnownIssue[]
  files: SeedFile[]
  zip: { name: string; bytes: number; url: string }
}

export const seedApi = {
  /** 404 seed_not_approved before Approve. */
  get: () => api<SeedPackage>('/api/seed'),
  /** 409 seed_approved, build_running, report_not_ready or iteration_superseded; 404 build_not_found. */
  approve: (buildId: string) => api<SeedPackage>('/api/seed/approve', { method: 'POST', json: { build_id: buildId } }),
}

/** A size as the cards show it: bytes under 1 KB, else KB with one decimal. */
export function size(bytes: number): string {
  return bytes < 1024 ? `${bytes.toLocaleString('en-US')} bytes` : `${(bytes / 1024).toFixed(1)} KB`
}

/** The approval's calendar date, "4 October 2026", in the viewer's own time zone. */
export function approvedOn(approvedAt: string | null): string {
  if (!approvedAt) return ''
  const when = new Date(approvedAt)
  return Number.isNaN(when.getTime()) ? '' : when.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
}
