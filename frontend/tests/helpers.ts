// Mount the whole app as main.ts does, on an in-memory history, without the live connection.

import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory } from 'vue-router'
import App from '../src/App.vue'
import { createAppRouter } from '../src/router'
import { useLabStore, type Snapshot } from '../src/stores/lab'

export function emptySnapshot(overrides: Partial<Snapshot> = {}): Snapshot {
  return {
    schema: 1,
    seq: 0,
    iteration: 1,
    next_file_id: 1,
    intake: { files: [] },
    builds: [],
    approval: null,
    ...overrides,
  }
}

export async function mountApp(path = '/', snapshot: Snapshot | null = null) {
  const pinia = createPinia()
  setActivePinia(pinia)
  useLabStore().snapshot = snapshot
  const router = createAppRouter(createMemoryHistory())
  await router.push(path)
  await router.isReady()
  const wrapper = mount(App, { global: { plugins: [pinia, router] }, attachTo: document.body })
  return { wrapper, router }
}
