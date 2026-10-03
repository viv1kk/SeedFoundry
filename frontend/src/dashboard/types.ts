// The dashboard as the server describes it (D-56): a descriptor that says what each panel is and
// how it looks, and a payload of every panel's data at one drill level, built from the seat rows.
// The frontend renders them and holds no analytical logic (seed-reuse-notes.md section 2.5).

export type Mark = 'kpi' | 'treemap' | 'bar' | 'line' | 'table'

/** The level ids one click appends to the drill path, as one step. */
export type Step = string[]

export interface ClassInfo {
  id: string
  label: string
  role: string
  recoverable: boolean
}

export interface Axis {
  name: string
  unit: string | null
}

export interface Series {
  id: string
  label: string
  role: string
}

export interface Column {
  id: string
  label: string
  format: string
  measure?: string
  align?: 'end'
  class?: string
  drill?: boolean
  font?: string
  null?: string
}

export interface Panel {
  id: string
  band: string
  title: string
  subtitle?: string
  caption?: string
  caption_role?: string
  mark: Mark
  span: number
  height?: number
  field?: string
  measure?: string
  format?: string
  emphasis?: 'primary'
  rule_role?: string
  note?: { text: string; role: string }
  legend?: { items: string; measure: string; format: string; of: string }
  orientation?: 'horizontal' | 'vertical'
  grouped?: boolean
  category?: { field: string; format?: string; axis: Axis }
  value?: { measure: string; format: string; axis: Axis }
  series?: Series[]
  withheld?: { label: string; role: string }
  drill?: boolean
  latency_ms?: number
  columns?: Column[]
  row_key?: string
  total_row?: boolean
  page_size?: number
  sortable?: boolean
  default_sort?: { column: string; direction: SortDirection }
  footer?: string
}

export interface Descriptor {
  id: string
  title: string
  variant: 'polished' | 'rough'
  classes: ClassInfo[]
  fonts: Record<string, string>
  grid: { columns: number; gutter: string }
  surface: string
  bands: { id: string; title: string }[]
  panels: Panel[]
}

export interface Crumb {
  label: string
  path: string
  levels: { kind: string; id: string; label: string }[]
}

export interface DrillInfo {
  path: string
  level: 'all' | 'vendor' | 'product' | 'class'
  depth: number
  deepest: boolean
  filter: { vendor: string | null; product: string | null; class: string | null }
  crumbs: Crumb[]
}

export interface Target {
  label: string
  value: number | null
  step: Step
}

export interface TreeNode {
  id: string
  name: string
  level: 'vendor' | 'product' | 'class'
  value: number
  class?: string
  step: Step | null
  children?: TreeNode[]
}

export interface Category {
  id: string
  name: string
  vendor: string
  step: Step | null
}

export type SortDirection = 'asc' | 'desc'

export type Row = Record<string, unknown> & { step?: Step | null }

export interface PanelData {
  value?: number
  withheld_seats?: number
  recoverable_seats?: number
  nodes?: TreeNode[]
  legend?: { class: string; label: string; count: number; share: number }[]
  total?: number | Row
  targets?: Target[]
  categories?: Category[]
  months?: string[]
  series?: Record<string, number[]>
  values?: (number | null)[]
  seats?: number[]
  withheld?: boolean[]
  rows?: Row[]
  page?: number
  pages?: number
  page_size?: number
  first?: number
  last?: number
  sort?: string
  direction?: SortDirection
  footer?: Record<string, number>
}

export interface Payload {
  dashboard: string
  dataset: { name: string; title: string; snapshot_date: string; period: { from: string; to: string }; seats: number }
  drill: DrillInfo
  panels: Record<string, PanelData>
}

export interface DashboardResponse {
  id: string
  iteration: number
  variant: string
  descriptor: Descriptor
  payload: Payload
}
