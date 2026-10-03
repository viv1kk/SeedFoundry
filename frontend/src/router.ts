// Routes (ui-spec.md section 1, D-38). The dashboard is not a route: it opens over the
// report at /review/:iteration?dashboard=license-optimization&drill=... (OQ-4, D-29).

import { createRouter, createWebHistory, type RouterHistory, type RouteRecordRaw } from 'vue-router'
import BuildView from './views/BuildView.vue'
import KnowledgeView from './views/KnowledgeView.vue'
import ReviewView from './views/ReviewView.vue'
import SeedView from './views/SeedView.vue'

/** Journey steps in order, by route name. The screen terms are the route names (requirements section 5). */
export const JOURNEY = ['knowledge', 'build', 'review', 'seed'] as const
export type JourneyStep = (typeof JOURNEY)[number]

// Two iterations only (D-6).
const ITERATION = ':iteration(1|2)'

export const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/knowledge' },
  { path: '/knowledge', name: 'knowledge', component: KnowledgeView },
  { path: `/build/${ITERATION}`, name: 'build', component: BuildView, props: true },
  { path: `/review/${ITERATION}`, name: 'review', component: ReviewView, props: true },
  { path: '/seed', name: 'seed', component: SeedView },
  { path: '/:unknown(.*)*', redirect: '/knowledge' },
]

export function createAppRouter(history: RouterHistory = createWebHistory()) {
  return createRouter({ history, routes })
}
