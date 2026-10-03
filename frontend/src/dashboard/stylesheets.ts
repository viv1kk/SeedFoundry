// The scoped stylesheets a descriptor may name (D-60). Only iteration 1's rough descriptor names
// one, defects.css, so it is loaded on demand, once, the first time that dashboard opens. Every
// rule in it sits under the root class the descriptor also names, so it reaches nothing else (R-1).

const SHEETS: Record<string, () => Promise<unknown>> = {
  'defects.css': () => import('../styles/defects.css'),
}

const loading = new Map<string, Promise<unknown>>()

/** Load a named sheet once; a name this app does not ship loads nothing. */
export function loadStylesheet(name: string): Promise<unknown> {
  const load = SHEETS[name]
  if (!load) return Promise.resolve()
  if (!loading.has(name)) loading.set(name, load())
  return loading.get(name)!
}
