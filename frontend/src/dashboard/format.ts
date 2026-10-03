// Number and text formats, one per measure, named by the descriptor (seed-reuse-notes.md section 1,
// environment.md Styling): counts with thousands separators; money in US dollars, compact on charts
// and KPIs and whole dollars in tables; percentages to one decimal place; ISO dates; months as
// "Oct 2025". The payload holds raw values, so the same value reads the same on every panel.
// `plain`, `compact` and `number` exist for the descriptor that names them (iteration 1's V-4,
// D-60); the polished descriptor names none of them.

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

const grouped = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 })

export function count(value: number): string {
  return grouped.format(value)
}

export function usd(value: number): string {
  return `$${grouped.format(value)}`
}

/** $850, $45k, $1.2M */
export function usdCompact(value: number): string {
  const size = Math.abs(value)
  if (size < 1000) return `$${grouped.format(value)}`
  const thousands = Math.round(value / 1000)
  if (Math.abs(thousands) < 1000) return `$${thousands}k`
  return `$${(value / 1_000_000).toFixed(1)}M`
}

/** 13050: no separators */
export function plain(value: number): string {
  return String(Math.round(value))
}

/** 850, 8.3k, 1.2M: no currency */
export function compact(value: number): string {
  const size = Math.abs(value)
  if (size < 1000) return String(Math.round(value))
  if (size < 1_000_000) return `${(value / 1000).toFixed(1)}k`
  return `${(value / 1_000_000).toFixed(1)}M`
}

export function percent(value: number): string {
  return `${value.toFixed(1)}%`
}

/** "2025-10" as "Oct 2025" */
export function month(value: string): string {
  const [year, number] = value.split('-')
  return `${MONTHS[Number(number) - 1] ?? number} ${year}`
}

export type Format = 'count' | 'number' | 'plain' | 'compact' | 'usd' | 'usd_compact' | 'percent' | 'month' | 'date' | 'id' | 'text' | 'class'

/** A value in a named format; null and missing values are the caller's to word. */
export function format(value: unknown, name: string): string {
  if (value === null || value === undefined) return ''
  switch (name) {
    case 'count':
    case 'number':
      return count(Number(value))
    case 'plain':
      return plain(Number(value))
    case 'compact':
      return compact(Number(value))
    case 'usd':
      return usd(Number(value))
    case 'usd_compact':
      return usdCompact(Number(value))
    case 'percent':
      return percent(Number(value))
    case 'month':
      return month(String(value))
    default:
      return String(value)
  }
}

/** An axis title: its name, and its unit in brackets unless the name already says it. */
export function axisTitle(axis: { name: string; unit: string | null }): string {
  if (!axis.unit || axis.name.toLowerCase().includes(axis.unit.toLowerCase())) return axis.name
  return `${axis.name} (${axis.unit})`
}
