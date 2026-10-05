// Intake API (D-35) and the rules the Knowledge page shares. Category ids, labels,
// descriptions and filename hints come from GET /api/intake/categories; nothing here
// copies them.

import { api } from './api'

export interface IntakeFile {
  id: string
  name: string
  category: string
  content: string
  size: number
}

/** An intake event's file: everything but the content (D-32). */
export type FileSummary = Omit<IntakeFile, 'content'>

export interface CategoryInfo {
  id: string
  label: string
  core: boolean
  description: string
  /** The name a file gets when it is added to this category (D-85). */
  file_name: string
  /** The Seed file shown beside it on the Knowledge page, a high-level picture only (D-86). */
  seed_file: string | null
}

export interface Categories {
  categories: CategoryInfo[]
  filename_hints: Record<string, string>
  max_file_bytes: number
}

const FILES = '/api/intake/files'

export const intakeApi = {
  categories: () => api<Categories>('/api/intake/categories'),
  read: (id: string) => api<IntakeFile>(`${FILES}/${encodeURIComponent(id)}`),
  create: (body: { name: string; category: string; content?: string; replace?: boolean }) =>
    api<IntakeFile>(FILES, { method: 'POST', json: body }),
  update: (
    id: string,
    changes: { name?: string; category?: string; content?: string; replace?: boolean },
    keepalive = false,
  ) => api<IntakeFile>(`${FILES}/${encodeURIComponent(id)}`, { method: 'PATCH', json: changes, keepalive }),
  remove: (id: string) => api<void>(`${FILES}/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  /** One file per request, its raw bytes as the body, so the server checks UTF-8 (D-34). */
  /** `name`, when given, is the name the file takes in Knowledge; the server checks `filename` (D-85). */
  import: (filename: string, raw: BodyInit, category: string, replace: boolean, name?: string) => {
    const query = new URLSearchParams({ filename, category, replace: String(replace), ...(name ? { name } : {}) })
    return api<IntakeFile>(`/api/intake/import?${query}`, { method: 'POST', body: raw })
  },
}

const encoder = new TextEncoder()

/** Size in UTF-8 bytes, as the server counts it (D-34). */
export function utf8Size(text: string): number {
  return encoder.encode(text).length
}

/** A core slot is complete when its file has something other than whitespace (FR-IN-8, D-42). */
export function isFilled(text: string): boolean {
  return text.trim() !== ''
}

/** The category the server's filename hints pre-select on import (FR-IN-7). */
export function hintedCategory(filename: string, hints: Record<string, string>, fallback: string): string {
  const base = filename.split(/[\\/]/).pop() ?? filename
  return hints[base.toLowerCase()] ?? fallback
}
