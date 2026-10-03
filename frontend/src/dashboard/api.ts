// The dashboard over /api (D-56). The query engine runs on the server: each drill level, page and
// sort is one request, and the answer holds the descriptor and every panel's data.

import { api } from '../api'
import type { DashboardResponse, SortDirection } from './types'

export const DASHBOARD_ID = 'license-optimization'

export interface DashboardQuery {
  iteration: number
  drill: string
  page: number
  sort?: string
  direction?: SortDirection
}

export function dashboardUrl(id: string, query: DashboardQuery): string {
  const params = new URLSearchParams({ iteration: String(query.iteration) })
  if (query.drill) params.set('drill', query.drill)
  if (query.page > 1) params.set('page', String(query.page))
  if (query.sort) params.set('sort', query.sort)
  if (query.direction) params.set('direction', query.direction)
  return `/api/dashboards/${encodeURIComponent(id)}?${params}`
}

export const dashboardApi = {
  get: (id: string, query: DashboardQuery) => api<DashboardResponse>(dashboardUrl(id, query)),
}
